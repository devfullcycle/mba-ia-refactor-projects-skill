const { verifyPassword, hashPassword } = require('../password');

class CheckoutService {
  constructor(conn, cache, config) {
    this.conn = conn;
    this.cache = cache;
    this.config = config;
  }

  async processCheckout(body) {
    const u = body.usr;
    const e = body.eml;
    const p = body.pwd;
    const cid = body.c_id;
    const cc = body.card;
    if (!u || !e || !cid || !cc) {
      const err = new Error('Bad Request');
      err.status = 400;
      throw err;
    }

    const course = await this.conn.get(`SELECT * FROM courses WHERE id = ? AND active = 1`, [cid]);
    if (!course) {
      const err = new Error('Curso não encontrado');
      err.status = 404;
      throw err;
    }

    const existing = await this.conn.get(`SELECT id, pass FROM users WHERE email = ?`, [e]);
    let userId;
    if (!existing) {
      const hash = hashPassword(p || '123456');
      const ins = await this.conn.run(`INSERT INTO users (name, email, pass) VALUES (?, ?, ?)`, [u, e, hash]);
      userId = ins.lastID;
    } else {
      if (!verifyPassword(p || '', existing.pass)) {
        const err = new Error('Credenciais inválidas');
        err.status = 401;
        throw err;
      }
      userId = existing.id;
    }

    if (this.config.paymentGatewayKey) {
      console.log(`Processando cartão (gateway configurado) curso=${cid}`);
    }

    const status = cc.startsWith('4') ? 'PAID' : 'DENIED';
    if (status === 'DENIED') {
      const err = new Error('Pagamento recusado');
      err.status = 400;
      throw err;
    }

    const enr = await this.conn.run(`INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)`, [userId, cid]);
    const enrId = enr.lastID;

    await this.conn.run(`INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)`, [
      enrId,
      course.price,
      status,
    ]);

    await this.conn.run(`INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))`, [
      `Checkout curso ${cid} por ${userId}`,
    ]);

    this.cache.set(`last_checkout_${userId}`, course.title);
    return { msg: 'Sucesso', enrollment_id: enrId };
  }
}

module.exports = { CheckoutService };
