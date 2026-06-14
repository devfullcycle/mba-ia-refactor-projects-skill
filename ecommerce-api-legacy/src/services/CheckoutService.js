const UserModel = require('../models/UserModel')
const CourseModel = require('../models/CourseModel')
const EnrollmentModel = require('../models/EnrollmentModel')
const PaymentModel = require('../models/PaymentModel')
const config = require('../config/settings')

class CheckoutService {
    constructor(db) {
        this.db = db
        this.userModel = new UserModel(db)
        this.courseModel = new CourseModel(db)
        this.enrollmentModel = new EnrollmentModel(db)
        this.paymentModel = new PaymentModel(db)
    }

    async processCheckout({ username, email, password, courseId, cardNumber }) {
        const course = await this.courseModel.findActiveById(courseId)
        if (!course) {
            const err = new Error('Curso não encontrado')
            err.status = 404
            throw err
        }

        let user = await this.userModel.findByEmail(email)
        const userId = user ? user.id : await this.userModel.create(username, email, password || '123456')

        const paymentStatus = await this._simulatePayment(cardNumber)
        if (paymentStatus === 'DENIED') {
            const err = new Error('Pagamento recusado')
            err.status = 402
            throw err
        }

        await this.db.runAsync('BEGIN TRANSACTION')
        try {
            const enrollmentId = await this.enrollmentModel.create(userId, courseId)
            await this.paymentModel.create(enrollmentId, course.price, paymentStatus)
            await this.db.runAsync(
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                [`Checkout: user ${userId} enrolled in course ${courseId}`]
            )
            await this.db.runAsync('COMMIT')
            return { enrollmentId }
        } catch (err) {
            await this.db.runAsync('ROLLBACK')
            throw err
        }
    }

    // TODO: Replace with real gateway SDK call using config.paymentGatewayKey
    async _simulatePayment(cardNumber) {
        if (!cardNumber || cardNumber.replace(/\s/g, '').length < 13) return 'DENIED'
        return 'PAID'
    }
}

module.exports = CheckoutService
