from werkzeug.security import check_password_hash, generate_password_hash

from models import usuario_model

_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def criar_usuario(nome, email, senha):
    return usuario_model.criar(nome, email, generate_password_hash(senha))


def autenticar(email, senha):
    """Retorna o usuário autenticado ou None.

    Senhas legadas em texto puro (bancos criados antes do hash) são aceitas
    uma única vez e regravadas com hash no mesmo login.
    """
    usuario = usuario_model.buscar_por_email(email)
    if usuario is None or not usuario["senha"]:
        return None

    armazenada = usuario["senha"]
    if armazenada.startswith(_PREFIXOS_HASH):
        return usuario if check_password_hash(armazenada, senha) else None

    if armazenada == senha:
        usuario_model.atualizar_senha(usuario["id"], generate_password_hash(senha))
        return usuario
    return None
