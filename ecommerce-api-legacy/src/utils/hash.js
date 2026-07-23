const bcrypt = require('bcrypt');
const config = require('../config');

const hashPassword = (plain) => bcrypt.hash(plain, config.bcryptRounds);
const verifyPassword = (plain, hash) => bcrypt.compare(plain, hash);

module.exports = { hashPassword, verifyPassword };
