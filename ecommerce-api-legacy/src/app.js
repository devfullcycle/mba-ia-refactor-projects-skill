const express = require('express')
const { port } = require('./config/settings')
const { initSchema } = require('./database/connection')
const checkoutRoutes = require('./routes/checkoutRoutes')
const reportRoutes = require('./routes/reportRoutes')
const userRoutes = require('./routes/userRoutes')
const { errorHandler } = require('./middlewares/errorHandler')

function createApp() {
  initSchema()

  const app = express()
  app.use(express.json())

  app.get('/', (req, res) => res.json({ msg: 'Frankenstein LMS API', version: '2.0.0' }))

  app.use('/api/checkout', checkoutRoutes)
  app.use('/api/admin', reportRoutes)
  app.use('/api/users', userRoutes)

  app.use(errorHandler)
  return app
}

if (require.main === module) {
  const app = createApp()
  app.listen(port, () => console.log(`LMS API rodando na porta ${port}`))
}

module.exports = { createApp }
