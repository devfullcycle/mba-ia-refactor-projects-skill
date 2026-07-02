from flask import jsonify
from models import pedido
from services import notificacao, relatorio
from utils.validators import validar_status_pedido
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)

def criar(dados):
    try:
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens or len(itens) == 0:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = pedido.criar(usuario_id, itens)

        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        notificacao.notificar_pedido_criado(resultado["pedido_id"], usuario_id)

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso"
        }), 201

    except Exception as e:
        logger.error(f"Erro ao criar pedido: {str(e)}")
        return jsonify({"erro": "Erro ao criar pedido"}), 500

def listar_por_usuario(usuario_id):
    try:
        pedidos = pedido.listar_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar pedidos: {str(e)}")
        return jsonify({"erro": "Erro ao listar pedidos"}), 500

def listar_todos():
    try:
        pedidos = pedido.listar_todos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar pedidos: {str(e)}")
        return jsonify({"erro": "Erro ao listar pedidos"}), 500

def atualizar_status(pedido_id, dados):
    try:
        novo_status = dados.get("status", "")

        erros = validar_status_pedido(novo_status)
        if erros:
            return jsonify({"erros": erros}), 400

        pedido.atualizar_status(pedido_id, novo_status)

        if novo_status == "aprovado":
            notificacao.notificar_pedido_aprovado(pedido_id)
        elif novo_status == "cancelado":
            notificacao.notificar_pedido_cancelado(pedido_id)

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    except Exception as e:
        logger.error(f"Erro ao atualizar status: {str(e)}")
        return jsonify({"erro": "Erro ao atualizar status"}), 500

def relatorio_vendas():
    try:
        relat = relatorio.gerar_relatorio_vendas()
        return jsonify({"dados": relat, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}")
        return jsonify({"erro": "Erro ao gerar relatório"}), 500
