class ReportController {
    constructor(reportService) {
        this._service = reportService;
    }

    async financialReport(req, res, next) {
        try {
            const report = await this._service.financialReport();
            res.json(report);
        } catch (err) {
            next(err);
        }
    }
}

module.exports = ReportController;
