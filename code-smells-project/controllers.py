"""Módulo de compatibilidade e facade para os controllers refatorados."""
from controllers.produto_controller import ProdutoController
from controllers.usuario_controller import UsuarioController
from controllers.pedido_controller import PedidoController
from controllers.relatorio_controller import RelatorioController
from controllers.health_controller import HealthController

listar_produtos = ProdutoController.listar_produtos
buscar_produto = ProdutoController.buscar_produto
buscar_produtos = ProdutoController.buscar_produtos
criar_produto = ProdutoController.criar_produto
atualizar_produto = ProdutoController.atualizar_produto
deletar_produto = ProdutoController.deletar_produto

listar_usuarios = UsuarioController.listar_usuarios
buscar_usuario = UsuarioController.buscar_usuario
criar_usuario = UsuarioController.criar_usuario
login = UsuarioController.login

criar_pedido = PedidoController.criar_pedido
listar_todos_pedidos = PedidoController.listar_todos_pedidos
listar_pedidos_usuario = PedidoController.listar_pedidos_usuario
atualizar_status_pedido = PedidoController.atualizar_status_pedido

relatorio_vendas = RelatorioController.relatorio_vendas
health_check = HealthController.health_check
index = HealthController.index
