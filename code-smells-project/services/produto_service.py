from services.excecoes import AppError


class ProdutoService:
    def __init__(self, produtos):
        self._produtos = produtos

    def listar(self):
        return self._produtos.listar()

    def obter(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if produto is None:
            raise AppError("Produto não encontrado", 404)
        return produto

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)

    def criar(self, dados):
        return self._produtos.criar(
            dados["nome"], dados["descricao"], dados["preco"], dados["estoque"], dados["categoria"]
        )

    def atualizar(self, produto_id, dados):
        self.obter(produto_id)
        self._produtos.atualizar(
            produto_id, dados["nome"], dados["descricao"], dados["preco"], dados["estoque"], dados["categoria"]
        )

    def remover(self, produto_id):
        self.obter(produto_id)
        self._produtos.remover(produto_id)
