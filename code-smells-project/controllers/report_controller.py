import models.report_model as report_model


def sales_report():
    relatorio = report_model.sales_report()
    return ({"dados": relatorio, "sucesso": True}, 200)


def health_check():
    data = report_model.health_data()
    data["versao"] = "1.0.0"
    return (data, 200)
