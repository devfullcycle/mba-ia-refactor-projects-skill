const enrollmentModel = require('../models/enrollmentModel')

function financialReport(req, res) {
  const rows = enrollmentModel.getFinancialReport()

  const coursesMap = {}
  for (const row of rows) {
    const cid = row.course_id
    if (!coursesMap[cid]) {
      coursesMap[cid] = { course: row.course_title, revenue: 0, students: [] }
    }
    if (row.payment_status === 'PAID') {
      coursesMap[cid].revenue += row.paid || 0
    }
    if (row.student_name) {
      coursesMap[cid].students.push({ student: row.student_name, paid: row.paid || 0 })
    }
  }

  res.json(Object.values(coursesMap))
}

module.exports = { financialReport }
