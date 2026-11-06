class EstoqueInsuficiente(Exception):
    def __init__(self, produto_id):
        super().__init__(produto_id)
        self.produto_id = produto_id


_SELECT_PEDIDOS = (
    "SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em, "
    "i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario, "
    "pr.id AS produto_existente, pr.nome AS produto_nome "
    "FROM pedidos p "
    "LEFT JOIN itens_pedido i ON i.pedido_id = p.id "
    "LEFT JOIN produtos pr ON pr.id = i.produto_id"
)


def _agrupar(linhas):
    pedidos = {}
    for linha in linhas:
        pedido = pedidos.get(linha["id"])
        if pedido is None:
            pedido = {
                "id": linha["id"],
                "usuario_id": linha["usuario_id"],
                "status": linha["status"],
                "total": linha["total"],
                "criado_em": linha["criado_em"],
                "itens": [],
            }
            pedidos[linha["id"]] = pedido
        if linha["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": linha["produto_id"],
                "produto_nome": linha["produto_nome"] if linha["produto_existente"] is not None else "Desconhecido",
                "quantidade": linha["quantidade"],
                "preco_unitario": linha["preco_unitario"],
            })
    return list(pedidos.values())


class PedidoModel:
    def __init__(self, banco):
        self._banco = banco

    def criar(self, usuario_id, itens, total):
        """Grava pedido, itens e baixa de estoque numa única transação (rollback em qualquer falha)."""
        conexao = self._banco.conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (usuario_id, total),
            )
            pedido_id = cursor.lastrowid
            for item in itens:
                baixa = conexao.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                )
                if baixa.rowcount == 0:
                    raise EstoqueInsuficiente(item["produto_id"])
                conexao.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                    "VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
                )
        return pedido_id

    def listar(self):
        linhas = self._banco.conexao().execute(_SELECT_PEDIDOS + " ORDER BY p.id, i.id").fetchall()
        return _agrupar(linhas)

    def listar_por_usuario(self, usuario_id):
        linhas = self._banco.conexao().execute(
            _SELECT_PEDIDOS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
        ).fetchall()
        return _agrupar(linhas)

    def atualizar_status(self, pedido_id, status):
        conexao = self._banco.conexao()
        with conexao:
            cursor = conexao.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
        return cursor.rowcount > 0

    def resumo_vendas(self):
        linha = self._banco.conexao().execute(
            "SELECT COUNT(*) AS total_pedidos, "
            "COALESCE(SUM(total), 0) AS faturamento, "
            "COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes, "
            "COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados, "
            "COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados "
            "FROM pedidos"
        ).fetchone()
        return dict(linha)
