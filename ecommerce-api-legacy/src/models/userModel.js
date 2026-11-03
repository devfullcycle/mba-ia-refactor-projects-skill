class UserModel {
  constructor(db) {
    this.db = db;
  }

  findById(id, conn = this.db) {
    return conn.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
  }

  findIdByEmail(email, conn = this.db) {
    return conn.get('SELECT id FROM users WHERE email = ?', [email]);
  }

  async create({ name, email, passwordHash }, conn = this.db) {
    const { lastID } = await conn.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
    return lastID;
  }

  /** Remove o usuário e seus dados dependentes (pagamentos e matrículas) na transação do chamador. */
  async deleteWithDependents(id, conn) {
    await conn.run(
      'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
      [id],
    );
    await conn.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
    const { changes } = await conn.run('DELETE FROM users WHERE id = ?', [id]);
    return changes > 0;
  }
}

module.exports = UserModel;
