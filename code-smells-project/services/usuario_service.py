"""Regras de negócio do domínio de usuários/autenticação."""

from models import usuario_model


class UsuarioInvalidoError(Exception):
    """Levantada quando os dados de usuário violam validações."""


def validar_dados_usuario(dados):
    if not dados:
        raise UsuarioInvalidoError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise UsuarioInvalidoError("Nome, email e senha são obrigatórios")
    return nome, email, senha


def criar(dados):
    nome, email, senha = validar_dados_usuario(dados)
    return usuario_model.criar_usuario(nome, email, senha)


def listar():
    return usuario_model.get_todos_usuarios()


def obter(usuario_id):
    return usuario_model.get_usuario_por_id(usuario_id)


def autenticar(dados):
    email = (dados or {}).get("email", "")
    senha = (dados or {}).get("senha", "")
    if not email or not senha:
        raise UsuarioInvalidoError("Email e senha são obrigatórios")
    return usuario_model.autenticar(email, senha)