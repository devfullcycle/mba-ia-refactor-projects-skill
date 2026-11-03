// Schema e seed do banco.
const SCHEMA = `
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT
  );
  CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER
  );
  CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id)
  );
  CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
    amount REAL,
    status TEXT
  );
  CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME
  );
`;

const SEED_COURSES = [
  ['Clean Architecture', 997.0, 1],
  ['Docker', 497.0, 1],
];

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };

async function createSchema(db) {
  await db.exec(SCHEMA);
}

async function seed(db, { hashPassword }) {
  const { count } = await db.get('SELECT COUNT(*) AS count FROM courses');
  if (count > 0) return;

  const passwordHash = await hashPassword(SEED_USER.password);
  await db.transaction(async (tx) => {
    const { lastID: userId } = await tx.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      [SEED_USER.name, SEED_USER.email, passwordHash],
    );
    const courseIds = [];
    for (const [title, price, active] of SEED_COURSES) {
      const { lastID } = await tx.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)', [title, price, active]);
      courseIds.push(lastID);
    }
    const { lastID: enrollmentId } = await tx.run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [userId, courseIds[0]],
    );
    await tx.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, SEED_COURSES[0][1], 'PAID']);
  });
}

module.exports = { createSchema, seed };
