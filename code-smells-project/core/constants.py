CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]

STATUS_PEDIDO = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


class DiscountPolicy:
    TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]

    @classmethod
    def rate_for(cls, amount):
        for threshold, rate in cls.TIERS:
            if amount > threshold:
                return rate
        return 0
