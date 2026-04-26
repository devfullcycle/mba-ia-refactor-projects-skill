const reportModel = require('../models/reportModel');

async function getFinancialReport(db) {
  const rows = await reportModel.getFinancialReport(db);

  const coursesMap = {};
  for (const row of rows) {
    if (!coursesMap[row.course_id]) {
      coursesMap[row.course_id] = {
        course: row.course_title,
        revenue: 0,
        students: [],
      };
    }
    const entry = coursesMap[row.course_id];
    if (row.student_name) {
      const paid = row.payment_status === 'PAID' ? row.payment_amount || 0 : 0;
      entry.revenue += paid;
      entry.students.push({ student: row.student_name, paid });
    }
  }

  return Object.values(coursesMap);
}

module.exports = { getFinancialReport };
