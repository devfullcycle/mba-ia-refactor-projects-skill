const ReportModel = require('../models/reportModel');

const getFinancialReport = async (req, res, next) => {
    try {
        const rows = await ReportModel.getFinancialReportData();

        // Group rows by course_id to construct the exact original structure
        const reportMap = {};

        rows.forEach(row => {
            const courseId = row.course_id;

            if (!reportMap[courseId]) {
                reportMap[courseId] = {
                    course: row.course_title,
                    revenue: 0,
                    students: []
                };
            }

            // If there's an enrollment, process user and payment details
            if (row.student_name !== null) {
                const paidAmount = row.payment_amount || 0;
                
                if (row.payment_status === 'PAID') {
                    reportMap[courseId].revenue += paidAmount;
                }

                reportMap[courseId].students.push({
                    student: row.student_name || 'Unknown',
                    paid: paidAmount
                });
            }
        });

        // Convert the map back to an array to match the expected format
        const report = Object.values(reportMap);

        return res.status(200).json(report);
    } catch (err) {
        next(err);
    }
};

module.exports = { getFinancialReport };
