const errorHandler = (err, req, res, next) => {
    console.error("[ERROR INTERNO INTERCEPTADO]:", err.stack || err);
    return res.status(500).send("Erro interno no servidor");
};

module.exports = errorHandler;
