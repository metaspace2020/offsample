from sqlalchemy import Column
from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from app import log
# from app.utils import alchemy

LOG = log.get_logger()


class BaseModel(object):
    # created = Column(DateTime, default=func.now())
    # modified = Column(DateTime, default=func.now(), onupdate=func.now())

    # @declared_attr
    # def __tablename__(self):
    #     return self.__name__.lower()

    @classmethod
    def find_one(cls, session, id):
        return session.query(cls).filter(cls.get_id() == id).one()

    @classmethod
    def find_first(cls, session, id):
        return session.query(cls).filter(cls.get_id() == id).first()

    @classmethod
    def find_update(cls, session, id, args):
        return session.query(cls).filter(cls.get_id() == id).update(args, synchronize_session=False)

    @classmethod
    def get_id(cls):
        pass

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in self.FIELDS}

    FIELDS = {
        # 'created': alchemy.datetime_to_timestamp,
        # 'modified': alchemy.datetime_to_timestamp,
    }

Base = declarative_base(cls=BaseModel)
