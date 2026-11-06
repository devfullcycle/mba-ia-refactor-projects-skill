from flask import request

from controllers import servicos
from controllers.validacao import validar_pedido, validar_status
from middlewares.auth import garantir_dono_ou_admin
from views.respostas import resposta
from views.serializers import pedido_publico


def criar():
    dados = validar_pedido(request.get_json(silent=True))
    garantir_dono_ou_admin(dados["usuario_id"])
    resultado = servicos().pedidos.criar(dados["usuario_id"], dados["itens"])
    return resposta(resultado, status=201, mensagem="Pedido criado com sucesso")


def listar_todos():
    return resposta([pedido_publico(p) for p in servicos().pedidos.listar_todos()])


def listar_do_usuario(usuario_id):
    garantir_dono_ou_admin(usuario_id)
    return resposta([pedido_publico(p) for p in servicos().pedidos.listar_do_usuario(usuario_id)])


def atualizar_status(pedido_id):
    status = validar_status(request.get_json(silent=True))
    servicos().pedidos.atualizar_status(pedido_id, status)
    return resposta(mensagem="Status atualizado")
