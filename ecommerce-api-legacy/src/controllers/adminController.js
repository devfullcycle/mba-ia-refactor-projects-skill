class AdminController {
    constructor({ financialReportService }) {
        this.financialReportService = financialReportService;
    }

    async financialReport(req, res) {
        const report = await this.financialReportService.build();
        res.json(report);
    }
}

module.exports = AdminController;
