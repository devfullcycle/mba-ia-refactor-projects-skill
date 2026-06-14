import sqlite3
from models.product_model import VALID_CATEGORIES

MAX_NOME_LENGTH = 200
MIN_NOME_LENGTH = 2


class ProductController:
    def __init__(self, product_model):
        self.product_model = product_model

    def list_all(self):
        return {"dados": self.product_model.find_all(), "sucesso": True}, 200

    def get_by_id(self, product_id):
        produto = self.product_model.find_by_id(product_id)
        if not produto:
            return {"erro": "Produto não encontrado", "sucesso": False}, 404
        return {"dados": produto, "sucesso": True}, 200

    def search(self, termo, categoria, preco_min, preco_max):
        try:
            if preco_min is not None:
                preco_min = float(preco_min)
            if preco_max is not None:
                preco_max = float(preco_max)
        except ValueError:
            return {"erro": "Preços devem ser numéricos"}, 400
        resultados = self.product_model.search(termo, categoria, preco_min, preco_max)
        return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200

    def create(self, data):
        if not data:
            return {"erro": "Dados inválidos"}, 400
        error = self._validate(data)
        if error:
            return {"erro": error}, 400
        try:
            product_id = self.product_model.create(
                data["nome"],
                data.get("descricao", ""),
                float(data["preco"]),
                int(data["estoque"]),
                data.get("categoria", "geral"),
            )
            return {"dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"}, 201
        except sqlite3.IntegrityError as e:
            return {"erro": str(e)}, 409
        except sqlite3.Error:
            return {"erro": "Erro de banco de dados"}, 500

    def update(self, product_id, data):
        if not self.product_model.find_by_id(product_id):
            return {"erro": "Produto não encontrado"}, 404
        if not data:
            return {"erro": "Dados inválidos"}, 400
        error = self._validate(data)
        if error:
            return {"erro": error}, 400
        try:
            self.product_model.update(
                product_id,
                data["nome"],
                data.get("descricao", ""),
                float(data["preco"]),
                int(data["estoque"]),
                data.get("categoria", "geral"),
            )
            return {"sucesso": True, "mensagem": "Produto atualizado"}, 200
        except sqlite3.Error:
            return {"erro": "Erro de banco de dados"}, 500

    def delete(self, product_id):
        if not self.product_model.find_by_id(product_id):
            return {"erro": "Produto não encontrado"}, 404
        try:
            self.product_model.delete(product_id)
            return {"sucesso": True, "mensagem": "Produto deletado"}, 200
        except sqlite3.Error:
            return {"erro": "Erro de banco de dados"}, 500

    def _validate(self, data):
        for field in ("nome", "preco", "estoque"):
            if field not in data:
                return f"{field.capitalize()} é obrigatório"
        nome = data["nome"]
        if len(nome) < MIN_NOME_LENGTH:
            return "Nome muito curto"
        if len(nome) > MAX_NOME_LENGTH:
            return "Nome muito longo"
        try:
            preco = float(data["preco"])
        except (TypeError, ValueError):
            return "Preço deve ser um número"
        if preco < 0:
            return "Preço não pode ser negativo"
        try:
            estoque = int(data["estoque"])
        except (TypeError, ValueError):
            return "Estoque deve ser um número inteiro"
        if estoque < 0:
            return "Estoque não pode ser negativo"
        categoria = data.get("categoria", "geral")
        if categoria not in VALID_CATEGORIES:
            return f"Categoria inválida. Válidas: {VALID_CATEGORIES}"
        return None
