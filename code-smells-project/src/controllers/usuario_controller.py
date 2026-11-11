import logging

from src.models import usuario_model
from src.services import auth_service
from src.utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from src.utils.validators import campo_texto

logger = logging.getLogger(__name__)


def is_admin(usuario):
    return usuario["tipo"] == usuario_model.TIPO_ADMIN


def verificar_acesso_ao_usuario(usuario_logado, usuario_id):
    """Cliente só acessa os próprios dados; admin acessa qualquer usuário."""
    if not is_admin(usuario_logado) and usuario_logado["id"] != usuario_id:
        raise ForbiddenError("Acesso negado aos dados de outro usuário")


def listar_usuarios():
    return usuario_model.listar()


def obter_usuario(usuario_id, usuario_logado):
    verificar_acesso_ao_usuario(usuario_logado, usuario_id)
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar_usuario(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    nome = campo_texto(dados, "nome")
    email = campo_texto(dados, "email").lower()
    senha = campo_texto(dados, "senha")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if "@" not in email:
        raise ValidationError("Email inválido")
    if usuario_model.email_existe(email):
        raise ConflictError("Email já cadastrado")

    try:
        usuario_id = usuario_model.criar(nome, email, senha)
    except usuario_model.EmailDuplicadoError:
        raise ConflictError("Email já cadastrado")
    logger.info("Usuário criado: id=%s", usuario_id)
    return usuario_id


def login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = campo_texto(dados, "email").lower()
    senha = campo_texto(dados, "senha")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        logger.info("Tentativa de login falhou")
        raise UnauthorizedError("Email ou senha inválidos")

    logger.info("Login bem-sucedido: usuario_id=%s", usuario["id"])
    return usuario, auth_service.gerar_token(usuario["id"])
