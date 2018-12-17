#!/usr/bin/env python
import argparse
import json
import logging
from time import sleep
import pika
import requests
from requests import ConnectionError
import yaml
from subprocess import check_output
from subprocess import CalledProcessError
import boto3
import datetime as dt


class ClusterDaemon(object):
    def __init__(self, ansible_config_path, aws_key_name=None, interval=60,
                 qname='sm_annotate', debug=False):

        with open(ansible_config_path) as fp:
            self.ansible_config = yaml.load(fp)

        self.interval = min(interval, 1200)
        self.aws_key_name = aws_key_name or self.ansible_config['aws_key_name']
        self.master_hostgroup = self.ansible_config['cluster_configuration']['instances']['master']['hostgroup']
        self.slave_hostgroup = self.ansible_config['cluster_configuration']['instances']['slave']['hostgroup']
        self.stage = self.ansible_config['stage']
        self.admin_email = self.ansible_config['notification_email']
        self.qname = qname
        self.debug = debug

        self._setup_logger()
        self.ec2 = boto3.resource('ec2', self.ansible_config['aws_region'])

    def _resolve_spark_master(self):
        self.logger.debug('Resolving spark master ip...')
        spark_master_instances = list(self.ec2.instances.filter(
            Filters=[{'Name': 'tag:hostgroup', 'Values': [self.master_hostgroup]},
                     {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'pending']}]))
        return spark_master_instances[0] if spark_master_instances else None

    @property
    def spark_master_public_ip(self):
        spark_master = self._resolve_spark_master()
        return spark_master.public_ip_address if spark_master else None

    @property
    def spark_master_private_ip(self):
        spark_master = self._resolve_spark_master()
        return spark_master.private_ip_address if spark_master else None

    def _setup_logger(self):
        self.logger = logging.getLogger('sm_cluster_auto_start')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)

    def _send_email(self, email, subj, body):
        ses = boto3.client('ses', 'eu-west-1')
        resp = ses.send_email(
            Source='contact@metaspace2020.eu',
            Destination={
                'ToAddresses': [email]
            },
            Message={
                'Subject': {
                    'Data': subj
                },
                'Body': {
                    'Text': {
                        'Data': body
                    }
                }
            }
        )
        if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
            self.logger.info('Email with "{}" subject was sent to {}'.format(subj, email))
        else:
            self.logger.warning('SEM failed to send email to {}'.format(email))

    def _send_rest_request(self, address):
        try:
            resp = requests.get(address)
        except ConnectionError as e:
            self.logger.debug('{} - {}'.format(address, e))
            return False
        except Exception as e:
            self.logger.warning('{} - {}'.format(address, e))
            return False
        else:
            self.logger.debug(resp)
            return resp.ok

    def queue_empty(self):
        creds = pika.PlainCredentials(self.ansible_config['rabbitmq_user'],
                                      self.ansible_config['rabbitmq_password'])
        conn = pika.BlockingConnection(pika.ConnectionParameters(host=self.ansible_config['rabbitmq_host'],
                                                                 credentials=creds))
        ch = conn.channel()
        m = ch.queue_declare(queue=self.qname, durable=True, arguments={'x-max-priority': 3})
        self.logger.debug('Messages in the queue: {}'.format(m.method.message_count))
        return m.method.message_count == 0

    def cluster_up(self):
        return self._send_rest_request('http://{}:8080/api/v1/applications'.format(self.spark_master_public_ip))

    def job_running(self):
        return self._send_rest_request('http://{}:4040/api/v1/applications'.format(self.spark_master_public_ip))

    def _local(self, command, success_msg=None, failed_msg=None):
        try:
            res = check_output(command)
            self.logger.debug(res)
            self.logger.info(success_msg)
        except CalledProcessError as e:
            self.logger.warning(e.output)
            self.logger.error(failed_msg)
            raise e

    def cluster_start(self):
        self.logger.info('Spinning up the cluster...')
        self._local(['ansible-playbook', '-i', self.stage, '-f', '1', 'aws_start.yml', '-e components=master,slave'],
                    'Cluster is spun up', 'Failed to spin up the cluster')

    def cluster_stop(self):
        self.logger.info('Stopping the cluster...')
        self._local(['ansible-playbook', '-i', self.stage, '-f', '1', 'aws_stop.yml', '-e', 'components=master,slave'],
                    'Cluster is stopped successfully', 'Failed to stop the cluster')

    def cluster_setup(self):
        self.logger.info('Setting up the cluster...')
        self._local(['ansible-playbook', '-i', self.stage, '-f', '1', 'aws_cluster_setup.yml'],
                    'Cluster setup is finished', 'Failed to set up the cluster')

    def sm_engine_deploy(self):
        self.logger.info('Deploying SM engine code...')
        self._local(['ansible-playbook', '-i', self.stage, '-f', '1', 'deploy/engine.yml'],
                    'The SM engine is deployed', 'Failed to deploy the SM engine')

    def _post_to_slack(self, emoji, msg):
        if not self.debug and self.ansible_config['slack_webhook_url']:
            msg = {
                "channel": self.ansible_config['slack_channel'],
                "username": "webhookbot",
                "text": ":{}: {}".format(emoji, msg),
                "icon_emoji": ":robot_face:"
            }
            requests.post(self.ansible_config['slack_webhook_url'], json=msg)

    def _ec2_hour_over(self):
        spark_instances = list(self.ec2.instances.filter(
            Filters=[{'Name': 'tag:hostgroup', 'Values': [self.master_hostgroup, self.slave_hostgroup]},
                     {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]))
        launch_time = min([i.launch_time for i in spark_instances])
        now_time = dt.datetime.utcnow()
        self.logger.debug('launch: {} now: {}'.format(launch_time, now_time))
        return 0 < (60 + (launch_time.minute - now_time.minute)) % 60 <= max(5, 2 * self.interval / 60)

    def _try_start_setup_deploy(self, setup_failed_max=5):
        setup_failed = 0
        while True:
            try:
                self.logger.info('Queue is not empty. Starting the cluster (%s attempt)...', setup_failed+1)
                self.cluster_start()
                m = {
                    'master': self.ansible_config['cluster_configuration']['instances']['master'],
                    'slave': self.ansible_config['cluster_configuration']['instances']['slave']
                }
                self._post_to_slack('rocket', "[v] Cluster started: {}".format(m))

                self.cluster_setup()
                self.sm_engine_deploy()
                self._post_to_slack('motorway', "[v] Cluster setup finished, SM engine deployed")
                sleep(60)
            except Exception as e:
                self.logger.warning('Failed to start/setup/deploy cluster: %s', e)
                setup_failed += 1
                if setup_failed >= setup_failed_max:
                    raise e
            else:
                break

    def start(self):
        self.logger.info('Started the SM cluster auto-start daemon (interval=%dsec)...', self.interval)
        try:
            while True:
                if not self.queue_empty():
                    if not self.cluster_up():
                        self._try_start_setup_deploy()
                else:
                    if self.cluster_up() and not self.job_running() and self._ec2_hour_over():
                        self.logger.info('Queue is empty. No jobs running. Stopping the cluster...')
                        self.cluster_stop()
                        self._post_to_slack('checkered_flag', "[v] Cluster stopped")

                sleep(self.interval)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            self._post_to_slack('sos', "[v] Something went wrong: {}".format(e))
            self._send_email(self.admin_email, 'Cluster auto start daemon ({}) failed'.format(self.stage), str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Daemon for auto starting SM cluster')
    parser.add_argument('--ansible-config', dest='ansible_config_path', default='env/dev/group_vars/all.yml', type=str,
                        help='Ansible config path')
    parser.add_argument('--interval', type=int, default=120, help='Cluster status check interval in sec (<1200)')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()

    cluster_daemon = ClusterDaemon(args.ansible_config_path, interval=args.interval,
                                   qname='sm_annotate', debug=args.debug)
    cluster_daemon.start()
