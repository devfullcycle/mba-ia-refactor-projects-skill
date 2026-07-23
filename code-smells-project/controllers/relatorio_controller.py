from services import relatorio_service


def relatorio_vendas():
    return {"dados": relatorio_service.sales_report(), "sucesso": True}, 200
