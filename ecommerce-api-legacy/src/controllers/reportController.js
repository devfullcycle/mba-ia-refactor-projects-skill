const { PAYMENT_STATUS } = require('../models/enrollmentModel');

class ReportController {
  constructor({ courseModel }) {
    this.courses = courseModel;
  }

  financialReport() {
    return this.courses.financialReport(PAYMENT_STATUS.PAID);
  }
}

module.exports = ReportController;
