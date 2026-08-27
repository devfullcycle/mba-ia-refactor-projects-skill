const { dbAll } = require('../database');

class ReportModel {
    static async getFinancialReportData() {
        const query = `
            SELECT 
                c.id AS course_id, 
                c.title AS course_title, 
                u.name AS student_name, 
                p.amount AS payment_amount, 
                p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON e.user_id = u.id
            LEFT JOIN payments p ON p.enrollment_id = e.id
        `;
        return await dbAll(query);
    }
}

module.exports = ReportModel;
