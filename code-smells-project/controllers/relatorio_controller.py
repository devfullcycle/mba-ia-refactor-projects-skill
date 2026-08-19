from flask import jsonify
from services.pedido_service import PedidoService

def relatorio_vendas():
    try:
        relatorio = PedidoService.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
