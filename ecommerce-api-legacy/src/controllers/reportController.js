const reportService = require('../services/reportService');

exports.financialReport = async (_req, res) => {
  const report = await reportService.financialReport();
  res.json(report);
};
