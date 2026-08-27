from flask import request, jsonify
from database import db
from models.produto import Produto

def listar_produtos():
    produtos = Produto.query.all()
    return jsonify({"dados": [p.to_dict() for p in produtos], "sucesso": True}), 200

def buscar_produto(id):
    produto = Produto.query.get(id)
    if produto:
        return jsonify({"dados": produto.to_dict(), "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404

def criar_produto():
    dados = request.get_json()
    if not dados or "nome" not in dados or "preco" not in dados or "estoque" not in dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    if dados["preco"] < 0 or dados["estoque"] < 0 or len(dados["nome"]) < 2 or len(dados["nome"]) > 200:
        return jsonify({"erro": "Dados inválidos"}), 400

    novo_produto = Produto(
        nome=dados["nome"],
        descricao=dados.get("descricao", ""),
        preco=dados["preco"],
        estoque=dados["estoque"],
        categoria=dados.get("categoria", "geral")
    )
    db.session.add(novo_produto)
    db.session.commit()
    return jsonify({"dados": {"id": novo_produto.id}, "sucesso": True, "mensagem": "Produto criado"}), 201

def atualizar_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = request.get_json()
    if not dados or "nome" not in dados or "preco" not in dados or "estoque" not in dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    produto.nome = dados["nome"]
    produto.descricao = dados.get("descricao", "")
    produto.preco = dados["preco"]
    produto.estoque = dados["estoque"]
    produto.categoria = dados.get("categoria", "geral")
    db.session.commit()
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

def deletar_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    db.session.delete(produto)
    db.session.commit()
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

def buscar_produtos():
    query = Produto.query
    termo = request.args.get("q")
    if termo:
        query = query.filter(Produto.nome.contains(termo) | Produto.descricao.contains(termo))
    categoria = request.args.get("categoria")
    if categoria:
        query = query.filter_by(categoria=categoria)
    preco_min = request.args.get("preco_min")
    if preco_min:
        query = query.filter(Produto.preco >= float(preco_min))
    preco_max = request.args.get("preco_max")
    if preco_max:
        query = query.filter(Produto.preco <= float(preco_max))

    resultados = query.all()
    return jsonify({"dados": [p.to_dict() for p in resultados], "total": len(resultados), "sucesso": True}), 200
