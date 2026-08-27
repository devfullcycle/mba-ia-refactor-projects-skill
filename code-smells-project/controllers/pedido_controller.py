from flask import request, jsonify
from services.pedido_service import PedidoService

def criar_pedido():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens or len(itens) == 0:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = PedidoService.criar(usuario_id, itens)

        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        # Simulating external services/notifications in a clean way
        # Print is okay as dummy but keeps the flow functioning
        print(f"ENVIANDO EMAIL: Pedido {resultado['pedido_id']} criado para usuario {usuario_id}")
        print("ENVIANDO SMS: Seu pedido foi recebido!")
        print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso"
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def listar_pedidos_usuario(usuario_id):
    try:
        pedidos = PedidoService.get_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def listar_todos_pedidos():
    try:
        pedidos = PedidoService.get_todos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json()
        novo_status = dados.get("status", "")

        if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]:
            return jsonify({"erro": "Status inválido"}), 400

        PedidoService.atualizar_status(pedido_id, novo_status)

        if novo_status == "aprovado":
            print(f"NOTIFICAÇÃO: Pedido {pedido_id} foi aprovado! Preparar envio.")
        elif novo_status == "cancelado":
            print(f"NOTIFICAÇÃO: Pedido {pedido_id} cancelado. Devolver estoque.")

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
