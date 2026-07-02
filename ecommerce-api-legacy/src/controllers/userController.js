class UserController {
    constructor({ userModel, enrollmentModel, paymentModel }) {
        this.userModel = userModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
    }

    deleteUser = async (req, res) => {
        const userId = Number(req.params.id);

        if (!Number.isInteger(userId) || userId <= 0) {
            return res.status(400).json({ error: 'id inválido' });
        }

        const enrollments = await this.enrollmentModel.findByUserId(userId);
        const enrollmentIds = enrollments.map((enrollment) => enrollment.id);

        await this.paymentModel.deleteByEnrollmentIds(enrollmentIds);
        await this.enrollmentModel.deleteByUserId(userId);
        await this.userModel.delete(userId);

        res.send('Usuário deletado com sucesso, incluindo matrículas e pagamentos associados.');
    };
}

module.exports = UserController;
