const bcrypt = require('bcrypt');

function secureCrypto(pwd) {
    // Correctly hashes using bcrypt for secure single-way cryptographic hash
    return bcrypt.hashSync(pwd, 10);
}

function logAndCache(key, val) {
    console.log(`[Cache Log] Cache key: ${key}, Value: ${val}`);
}

module.exports = { secureCrypto, logAndCache };
