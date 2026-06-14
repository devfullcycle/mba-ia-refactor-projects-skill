import sqlite3
from models.order_model import VALID_STATUSES

DISCOUNT_TIER_PREMIUM = 10000
DISCOUNT_TIER_STANDARD = 5000
DISCOUNT_TIER_BASE = 1000
DISCOUNT_RATE_PREMIUM = 0.10
DISCOUNT_RATE_STANDARD = 0.05
DISCOUNT_RATE_BASE = 0.02


class OrderController:
    def __init__(self, order_model):
        self.order_model = order_model

    def create(self, data):
        if not data:
            return {"erro": "Dados inválidos"}, 400
        usuario_id = data.get("usuario_id")
        itens = data.get("itens", [])
        if not usuario_id:
            return {"erro": "Usuario ID é obrigatório"}, 400
        if not itens:
            return {"erro": "Pedido deve ter pelo menos 1 item"}, 400
        resultado = self.order_model.create(usuario_id, itens)
        if "erro" in resultado:
            return {"erro": resultado["erro"], "sucesso": False}, 400
        return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201

    def list_by_user(self, usuario_id):
        pedidos = self.order_model.find_by_user(usuario_id)
        return {"dados": pedidos, "sucesso": True}, 200

    def list_all(self):
        pedidos = self.order_model.find_all()
        return {"dados": pedidos, "sucesso": True}, 200

    def update_status(self, pedido_id, data):
        if not data:
            return {"erro": "Dados inválidos"}, 400
        novo_status = data.get("status", "")
        if novo_status not in VALID_STATUSES:
            return {"erro": "Status inválido"}, 400
        try:
            self.order_model.update_status(pedido_id, novo_status)
            return {"sucesso": True, "mensagem": "Status atualizado"}, 200
        except sqlite3.Error:
            return {"erro": "Erro de banco de dados"}, 500

    def sales_report(self):
        relatorio = self.order_model.sales_report()
        faturamento = relatorio["faturamento_bruto"]
        desconto = self._calculate_discount(faturamento)
        relatorio["desconto_aplicavel"] = round(desconto, 2)
        relatorio["faturamento_liquido"] = round(faturamento - desconto, 2)
        return {"dados": relatorio, "sucesso": True}, 200

    def _calculate_discount(self, faturamento):
        if faturamento > DISCOUNT_TIER_PREMIUM:
            return faturamento * DISCOUNT_RATE_PREMIUM
        if faturamento > DISCOUNT_TIER_STANDARD:
            return faturamento * DISCOUNT_RATE_STANDARD
        if faturamento > DISCOUNT_TIER_BASE:
            return faturamento * DISCOUNT_RATE_BASE
        return 0.0
