const userModel = require('../models/userModel')
const courseModel = require('../models/courseModel')
const enrollmentModel = require('../models/enrollmentModel')
const paymentService = require('../services/paymentService')
const { db } = require('../database/connection')

function checkout(req, res) {
  const { username, email, password, course_id, card_number } = req.body

  if (!username || !email || !course_id || !card_number) {
    return res.status(400).json({ error: 'username, email, course_id e card_number são obrigatórios' })
  }

  const course = courseModel.findById(course_id)
  if (!course) {
    return res.status(404).json({ error: 'Curso não encontrado ou inativo' })
  }

  const payment = paymentService.processPayment(card_number, course.price)
  if (payment.status === 'DENIED') {
    return res.status(400).json({ error: 'Pagamento recusado' })
  }

  let user = userModel.findByEmail(email)
  if (!user) {
    const userId = userModel.create(username, email, password || '123456')
    user = { id: userId }
  }

  const enrollmentId = enrollmentModel.create(user.id, course_id)
  enrollmentModel.createPayment(enrollmentId, course.price, payment.status)

  db.prepare(
    "INSERT INTO audit_logs (action) VALUES (?)"
  ).run(`Checkout curso ${course_id} por usuário ${user.id}`)

  res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId })
}

module.exports = { checkout }
