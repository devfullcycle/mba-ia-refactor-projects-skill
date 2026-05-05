class UserService {
  constructor(conn) {
    this.conn = conn;
  }

  async deleteUser(id) {
    const enrollments = await this.conn.all(`SELECT id FROM enrollments WHERE user_id = ?`, [id]);
    for (const row of enrollments) {
      await this.conn.run(`DELETE FROM payments WHERE enrollment_id = ?`, [row.id]);
    }
    await this.conn.run(`DELETE FROM enrollments WHERE user_id = ?`, [id]);
    await this.conn.run(`DELETE FROM users WHERE id = ?`, [id]);
    return { ok: true, message: 'Usuário e matrículas relacionadas removidos.' };
  }
}

module.exports = { UserService };
