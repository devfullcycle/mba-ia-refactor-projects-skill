"""Small protocol-independent value objects used by application services."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ValidationError


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: int
    role: str
    email: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@dataclass(frozen=True, slots=True)
class ProductInput:
    nome: str
    descricao: str
    preco: float
    estoque: int
    categoria: str

    @classmethod
    def from_mapping(cls, data: object) -> "ProductInput":
        if not isinstance(data, dict):
            raise ValidationError("Dados inválidos")
        required = ("nome", "preco", "estoque")
        missing = next((field for field in required if field not in data), None)
        if missing:
            labels = {"nome": "Nome", "preco": "Preço", "estoque": "Estoque"}
            raise ValidationError(f"{labels[missing]} é obrigatório")

        nome = data["nome"]
        descricao = data.get("descricao", "")
        categoria = data.get("categoria", "geral")
        if not isinstance(nome, str) or not isinstance(descricao, str) or not isinstance(categoria, str):
            raise ValidationError("Nome, descrição e categoria devem ser texto")
        if not isinstance(data["preco"], (int, float)) or isinstance(data["preco"], bool):
            raise ValidationError("Preço deve ser numérico")
        if not isinstance(data["estoque"], int) or isinstance(data["estoque"], bool):
            raise ValidationError("Estoque deve ser inteiro")
        value = cls(nome, descricao, float(data["preco"]), data["estoque"], categoria)
        value.validate()
        return value

    def validate(self) -> None:
        if not 2 <= len(self.nome) <= 200:
            raise ValidationError("Nome deve conter entre 2 e 200 caracteres")
        if self.preco < 0:
            raise ValidationError("Preço não pode ser negativo")
        if self.estoque < 0:
            raise ValidationError("Estoque não pode ser negativo")
        if self.categoria not in {"informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"}:
            raise ValidationError("Categoria inválida")


@dataclass(frozen=True, slots=True)
class OrderItemInput:
    produto_id: int
    quantidade: int

    @classmethod
    def from_mapping(cls, data: object) -> "OrderItemInput":
        if not isinstance(data, dict):
            raise ValidationError("Item de pedido inválido")
        produto_id = data.get("produto_id")
        quantidade = data.get("quantidade")
        if not isinstance(produto_id, int) or isinstance(produto_id, bool) or not isinstance(quantidade, int) or isinstance(quantidade, bool):
            raise ValidationError("produto_id e quantidade devem ser inteiros")
        if produto_id <= 0 or quantidade <= 0:
            raise ValidationError("Produto e quantidade devem ser positivos")
        return cls(produto_id, quantidade)


# Names retained for callers that imported the pre-refactor domain objects.
ProductData = ProductInput
OrderItem = OrderItemInput
