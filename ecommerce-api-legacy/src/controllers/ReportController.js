const { getDb } = require('../database')

async function getFinancialReport(req, res, next) {
    try {
        const db = getDb()
        const rows = await db.allAsync(`
            SELECT
                c.id     AS course_id,
                c.title  AS course_title,
                u.name   AS student_name,
                p.amount AS payment_amount,
                p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u       ON u.id = e.user_id
            LEFT JOIN payments p    ON p.enrollment_id = e.id
            ORDER BY c.id
        `)

        const reportMap = {}
        for (const row of rows) {
            if (!reportMap[row.course_id]) {
                reportMap[row.course_id] = { course: row.course_title, revenue: 0, students: [] }
            }
            if (row.student_name) {
                if (row.payment_status === 'PAID') {
                    reportMap[row.course_id].revenue += row.payment_amount
                }
                reportMap[row.course_id].students.push({
                    student: row.student_name,
                    paid: row.payment_amount || 0,
                })
            }
        }

        res.json(Object.values(reportMap))
    } catch (err) {
        next(err)
    }
}

module.exports = { getFinancialReport }
