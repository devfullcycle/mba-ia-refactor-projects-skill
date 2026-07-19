// Controller magro do relatório financeiro: delega ao service e serializa o JSON.
class ReportController {
    constructor({ reportService }) {
        this.reportService = reportService;
        this.financialReport = this.financialReport.bind(this);
    }

    async financialReport(req, res, next) {
        try {
            const report = await this.reportService.financialReport();
            res.status(200).json(report);
        } catch (err) {
            next(err);
        }
    }
}

module.exports = ReportController;
