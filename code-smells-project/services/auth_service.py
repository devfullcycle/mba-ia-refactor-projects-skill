from itsdangerous import BadSignature, URLSafeTimedSerializer


class AuthService:
    """Emite e valida tokens assinados com a SECRET_KEY (expiração em segundos)."""

    def __init__(self, secret_key, max_age, usuario_service):
        self._serializador = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._max_age = max_age
        self._usuarios = usuario_service

    def login(self, email, senha):
        usuario = self._usuarios.autenticar(email, senha)
        if usuario is None:
            return None
        return usuario, self._serializador.dumps({"id": usuario["id"]})

    def usuario_do_token(self, token):
        try:
            dados = self._serializador.loads(token, max_age=self._max_age)
        except BadSignature:
            return None
        if not isinstance(dados, dict):
            return None
        return self._usuarios.buscar(dados.get("id"))
