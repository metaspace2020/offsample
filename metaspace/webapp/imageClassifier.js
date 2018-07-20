const {mapValues, keyBy} = require('lodash');

const configureKnex = async () => {
  const knex = require('knex')({
    client: 'sqlite3',
    connection: {
      filename: './imageclassification.sqlite',
    },
    useNullAsDefault: true,
  });

  if (!await knex.schema.hasTable('imageclassifications')) {
    await knex.schema.createTable('imageclassifications', (table) => {
      table.increments();
      table.string('datasetId');
      table.string('user');
      table.string('annotationId');
      table.string('sumFormula');
      table.string('adduct');
      table.string('msmScore');
      table.string('fdrLevel');
      table.string('mz');
      table.string('ionImageUrl');
      table.int('type');
      table.unique(['datasetId','user','annotationId']);
    });
  }

  return knex;
};

const configureImageClassifier = async (app) => {
  const knex = await configureKnex();

  app.get('/imageclassifier', async (req, res, next) => {
    try {
      const { datasetId, user } = req.query;
      if (!datasetId || !user) {
        next();
      }
      const results = await knex('imageclassifications').where({ datasetId, user });
      res.send(mapValues(keyBy(results, 'annotationId'), 'type'));
    } catch (err) {
      next(err);
    }
  });

  app.post('/imageclassifier', async (req, res, next) => {
    try {
      const { datasetId, user, annotationId, ...rest } = req.body;
      if ((await knex('imageclassifications').where({ datasetId, user, annotationId })).length > 0) {
        await knex('imageclassifications').where({ datasetId, user, annotationId }).update({ ...rest });
      } else {
        await knex('imageclassifications').insert({ datasetId, user, annotationId, ...rest });
      }
      res.send();
    } catch (err) {
      next(err);
    }
  })
};


module.exports = {
  configureImageClassifier
};
