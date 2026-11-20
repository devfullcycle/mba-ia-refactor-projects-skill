from ..models.pedido_model import PedidoModel
from ..models.produto_model import ProdutoModel
from ..models.usuario_model import UsuarioModel


class SistemaController:
    def __init__(self, produtos: ProdutoModel, usuarios: UsuarioModel, pedidos: PedidoModel,
                 versao: str, ambiente: str):
        self.produtos = produtos
        self.usuarios = usuarios
        self.pedidos = pedidos
        self.versao = versao
        self.ambiente = ambiente

    def info(self) -> dict:
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self.versao,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }

    def health(self) -> dict:
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self.produtos.contar(),
                "usuarios": self.usuarios.contar(),
                "pedidos": self.pedidos.contar(),
            },
            "versao": self.versao,
            "ambiente": self.ambiente,
        }
