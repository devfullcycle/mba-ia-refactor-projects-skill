from controllers import servicos
from views.respostas import resposta


def vendas():
    return resposta(servicos().relatorios.vendas())
