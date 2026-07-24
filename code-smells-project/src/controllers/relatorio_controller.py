"""Controller de Relatórios — consultas analíticas do domínio de vendas."""


class RelatorioController:
    def __init__(self, pedido_model):
        self._pedidos = pedido_model

    def vendas(self):
        return {"dados": self._pedidos.sales_report(), "sucesso": True}, 200
