// Mantém os nomes públicos da API (contrato do legado).
function toCheckoutInput(body = {}) {
    return { name: body.usr, email: body.eml, password: body.pwd, courseId: body.c_id, cardNumber: body.card };
}

function presentCheckout({ enrollmentId }) {
    return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

module.exports = { toCheckoutInput, presentCheckout };
