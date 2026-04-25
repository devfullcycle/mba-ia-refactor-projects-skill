import config.settings as settings
import models.product_model as product_model


def validate_product(dados):
    if not dados:
        return ("Dados invalidos", 400)
    if "nome" not in dados:
        return ("Nome e obrigatorio", 400)
    if "preco" not in dados:
        return ("Preco e obrigatorio", 400)
    if "estoque" not in dados:
        return ("Estoque e obrigatorio", 400)

    preco = dados["preco"]
    estoque = dados["estoque"]
    nome = dados["nome"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        return ("Preco nao pode ser negativo", 400)
    if estoque < 0:
        return ("Estoque nao pode ser negativo", 400)
    if len(nome) < 2:
        return ("Nome muito curto", 400)
    if len(nome) > 200:
        return ("Nome muito longo", 400)
    if categoria not in settings.VALID_CATEGORIES:
        return (f"Categoria invalida. Validas: {settings.VALID_CATEGORIES}", 400)

    return None


def list_all():
    produtos = product_model.get_all()
    return ({"dados": produtos, "sucesso": True}, 200)


def get_by_id(product_id):
    produto = product_model.get_by_id(product_id)
    if produto:
        return ({"dados": produto, "sucesso": True}, 200)
    return ({"erro": "Produto nao encontrado", "sucesso": False}, 404)


def create(dados):
    error = validate_product(dados)
    if error:
        return ({"erro": error[0]}, error[1])

    product_id = product_model.create(
        nome=dados["nome"],
        descricao=dados.get("descricao", ""),
        preco=dados["preco"],
        estoque=dados["estoque"],
        categoria=dados.get("categoria", "geral"),
    )
    return ({"dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"}, 201)


def update(product_id, dados):
    existing = product_model.get_by_id(product_id)
    if not existing:
        return ({"erro": "Produto nao encontrado"}, 404)

    error = validate_product(dados)
    if error:
        return ({"erro": error[0]}, error[1])

    product_model.update(
        product_id=product_id,
        nome=dados["nome"],
        descricao=dados.get("descricao", ""),
        preco=dados["preco"],
        estoque=dados["estoque"],
        categoria=dados.get("categoria", "geral"),
    )
    return ({"sucesso": True, "mensagem": "Produto atualizado"}, 200)


def delete(product_id):
    existing = product_model.get_by_id(product_id)
    if not existing:
        return ({"erro": "Produto nao encontrado"}, 404)

    product_model.delete(product_id)
    return ({"sucesso": True, "mensagem": "Produto deletado"}, 200)


def search(term, category=None, price_min=None, price_max=None):
    resultados = product_model.search(term, category, price_min, price_max)
    return ({"dados": resultados, "total": len(resultados), "sucesso": True}, 200)
