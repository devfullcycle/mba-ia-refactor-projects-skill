// Wrapper Promise sobre o driver sqlite3 com transações serializadas.
const sqlite3 = require('sqlite3');

class Database {
  constructor(driver) {
    this.driver = driver;
    this.transactionQueue = Promise.resolve();
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.driver.run(sql, params, function onRun(err) {
        if (err) return reject(err);
        return resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.driver.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.driver.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
  }

  exec(sql) {
    return new Promise((resolve, reject) => {
      this.driver.exec(sql, (err) => (err ? reject(err) : resolve()));
    });
  }

  /**
   * Executa `work` atomicamente (BEGIN/COMMIT/ROLLBACK). As transações são enfileiradas
   * porque a conexão SQLite é única e não suporta transações aninhadas/concorrentes.
   */
  transaction(work) {
    const execute = async () => {
      await this.run('BEGIN');
      try {
        const result = await work(this);
        await this.run('COMMIT');
        return result;
      } catch (err) {
        await this.run('ROLLBACK');
        throw err;
      }
    };
    const result = this.transactionQueue.then(execute, execute);
    this.transactionQueue = result.catch(() => {});
    return result;
  }

  close() {
    return new Promise((resolve, reject) => this.driver.close((err) => (err ? reject(err) : resolve())));
  }
}

async function createDatabase({ filename, verbose }) {
  const driverModule = verbose ? sqlite3.verbose() : sqlite3;
  const driver = await new Promise((resolve, reject) => {
    const conn = new driverModule.Database(filename, (err) => (err ? reject(err) : resolve(conn)));
  });
  const db = new Database(driver);
  await db.run('PRAGMA foreign_keys = ON');
  return db;
}

module.exports = { createDatabase, Database };
