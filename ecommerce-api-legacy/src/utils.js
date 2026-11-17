const config = require('./config/config');
const security = require('./utils/security');

// Wrapper de compatibilidade segura para módulos legados
function logAndCache(key, data) {
    // Encapsulado sem estado global vulnerável
    console.log(`[LOG] Cache simulado para a chave: ${key}`);
}

function badCrypto(pwd) {
    // Mapeado para implementação segura com salt
    return security.hashPassword(pwd);
}

module.exports = {
    config,
    logAndCache,
    badCrypto,
    ...security
};
