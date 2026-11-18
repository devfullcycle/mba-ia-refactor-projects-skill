module.exports = ({ reportService }) => ({
    async financial(req, res) {
        res.json(await reportService.financialReport());
    }
});
