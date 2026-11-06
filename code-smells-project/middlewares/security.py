from flask_cors import CORS

CABECALHOS_SEGURANCA = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


def registrar_seguranca_http(app, origens_cors):
    # Lista vazia = nenhuma origem externa recebe Access-Control-Allow-Origin.
    CORS(app, origins=origens_cors)

    @app.after_request
    def _cabecalhos(resposta):
        for nome, valor in CABECALHOS_SEGURANCA.items():
            resposta.headers.setdefault(nome, valor)
        return resposta
