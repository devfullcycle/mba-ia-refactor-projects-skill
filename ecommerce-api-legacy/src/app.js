const express = require('express')
const config = require('./config/settings')
const { initDb } = require('./database')
const checkoutRoutes = require('./routes/checkoutRoutes')
const reportRoutes = require('./routes/reportRoutes')
const userRoutes = require('./routes/userRoutes')
const errorHandler = require('./middlewares/errorHandler')

const app = express()
app.use(express.json())

app.use('/api/checkout', checkoutRoutes)
app.use('/api/admin', reportRoutes)
app.use('/api/users', userRoutes)

app.use(errorHandler)

initDb()
    .then(() => {
        app.listen(config.port, () => {
            console.log(`LMS API running on port ${config.port}`)
        })
    })
    .catch(err => {
        console.error('Failed to initialize database:', err)
        process.exit(1)
    })
