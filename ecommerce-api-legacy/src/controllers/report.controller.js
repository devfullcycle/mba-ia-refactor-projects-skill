'use strict';

class ReportController {
    constructor({ reportService }) {
        this.service = reportService;
    }

    financial = async (_req, res, next) => {
        try {
            const report = await this.service.financialReport();
            res.status(200).json(report);
        } catch (error) {
            next(error);
        }
    };
}

module.exports = { ReportController };
