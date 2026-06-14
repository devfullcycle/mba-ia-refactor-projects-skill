const UserModel = require('../models/UserModel')
const { getDb } = require('../database')

async function deleteUser(req, res, next) {
    const id = parseInt(req.params.id, 10)

    if (!Number.isInteger(id) || id <= 0) {
        return res.status(400).json({ error: 'Invalid user ID' })
    }

    try {
        const userModel = new UserModel(getDb())
        const user = await userModel.findById(id)
        if (!user) {
            return res.status(404).json({ error: 'User not found' })
        }
        await userModel.deleteById(id)
        res.json({ msg: 'User and associated records deleted successfully' })
    } catch (err) {
        next(err)
    }
}

module.exports = { deleteUser }
