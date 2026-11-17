"""Módulo de compatibilidade e facade para os models refatorados."""
from models.produto_model import ProdutoModel
from models.usuario_model import UsuarioModel
from models.pedido_model import PedidoModel
from models.relatorio_model import RelatorioModel
from models.database import get_db

get_todos_produtos = ProdutoModel.listar_todos
get_produto_por_id = ProdutoModel.buscar_por_id
buscar_produtos = ProdutoModel.buscar
criar_produto = ProdutoModel.criar
atualizar_produto = ProdutoModel.atualizar
deletar_produto = ProdutoModel.deletar

get_todos_usuarios = UsuarioModel.listar_todos
get_usuario_por_id = UsuarioModel.buscar_por_id
criar_usuario = UsuarioModel.criar
login_usuario = UsuarioModel.autenticar

criar_pedido = PedidoModel.criar
get_todos_pedidos = PedidoModel.listar_todos
get_pedidos_usuario = PedidoModel.listar_por_usuario
atualizar_status_pedido = PedidoModel.atualizar_status

relatorio_vendas = RelatorioModel.obter_resumo_vendas
