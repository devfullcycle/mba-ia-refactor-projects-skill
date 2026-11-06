"""Composition root: cria a aplicação, monta dependências, registra rotas e middlewares."""
import logging
import secrets
from types import SimpleNamespace

from flask import Flask

from config.logging_config import configurar_logging
from config.settings import Settings
from database.connection import BancoDados
from database.schema import criar_schema
from database.seed import semear
from middlewares.error_handler import registrar_tratamento_erros
from middlewares.security import registrar_seguranca_http
from models.pedido_model import PedidoModel
from models.produto_model import ProdutoModel
from models.sistema_model import SistemaModel
from models.usuario_model import UsuarioModel
from routes import registrar_rotas
from services.auth_service import AuthService
from services.notificacao_service import NotificacaoService
from services.pedido_service import PedidoService
from services.produto_service import ProdutoService
from services.relatorio_service import RelatorioService
from services.sistema_service import SistemaService
from services.usuario_service import UsuarioService, gerar_hash_senha

logger = logging.getLogger("app")


def _chave_secreta(settings):
    if settings.secret_key:
        return settings.secret_key
    logger.warning("SECRET_KEY não definida: usando chave aleatória temporária (tokens expiram ao reiniciar)")
    return secrets.token_hex(32)


def _montar_servicos(settings, banco, chave):
    produtos = ProdutoModel(banco)
    usuarios = UsuarioModel(banco)
    pedidos = PedidoModel(banco)
    usuario_service = UsuarioService(usuarios)
    return SimpleNamespace(
        produtos=ProdutoService(produtos),
        usuarios=usuario_service,
        auth=AuthService(chave, settings.token_max_age, usuario_service),
        pedidos=PedidoService(pedidos, produtos, usuarios, NotificacaoService()),
        relatorios=RelatorioService(pedidos),
        sistema=SistemaService(SistemaModel(banco), settings.allow_destructive),
    )


def create_app(settings=None):
    settings = settings or Settings()
    configurar_logging(settings.log_level)

    app = Flask(__name__)
    chave = _chave_secreta(settings)
    app.config["SECRET_KEY"] = chave
    app.config["DEBUG"] = settings.debug

    def inicializar_banco(conexao):
        criar_schema(conexao)
        semear(conexao, settings, gerar_hash_senha)

    banco = BancoDados(settings.db_path, inicializador=inicializar_banco)
    app.teardown_appcontext(banco.fechar)
    app.extensions["settings"] = settings
    app.extensions["banco"] = banco
    app.extensions["servicos"] = _montar_servicos(settings, banco, chave)

    registrar_seguranca_http(app, settings.cors_origins)
    registrar_tratamento_erros(app)
    registrar_rotas(app)
    return app


app = create_app()

if __name__ == "__main__":
    configuracao = app.extensions["settings"]
    with app.app_context():
        app.extensions["banco"].conexao()  # cria schema e seed no boot
    logger.info("Servidor iniciado em http://%s:%s", configuracao.host, configuracao.port)
    app.run(host=configuracao.host, port=configuracao.port, debug=configuracao.debug)
