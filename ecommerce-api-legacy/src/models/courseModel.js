const db = require('../config/database');

const CourseModel = {
    findActiveById(id) {
        return db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]);
    },

    async count() {
        const row = await db.get('SELECT COUNT(*) AS total FROM courses');
        return row.total;
    },

    async create({ title, price, active = 1 }) {
        const { lastID } = await db.run(
            'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
            [title, price, active],
        );
        return lastID;
    },

    // Uma única query (em vez de 1 + C + 2·E) com uma linha por matrícula; cursos sem matrícula vêm com enrollment_id NULL.
    findFinancialRows() {
        return db.all(
            `SELECT c.id AS course_id,
                    c.title AS course_title,
                    e.id AS enrollment_id,
                    u.name AS student_name,
                    p.amount AS payment_amount,
                    p.status AS payment_status
               FROM courses c
               LEFT JOIN enrollments e ON e.course_id = c.id
               LEFT JOIN users u ON u.id = e.user_id
               LEFT JOIN payments p ON p.enrollment_id = e.id
              ORDER BY c.id, e.id`,
        );
    },
};

module.exports = CourseModel;
