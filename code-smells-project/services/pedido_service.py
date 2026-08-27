from database import db
from models.pedido import Pedido, ItemPedido
from models.produto import Produto

class PedidoService:
    @staticmethod
    def criar(usuario_id, itens):
        # 1. Validar produtos e calcular total
        total = 0
        lista_itens = []
        for item in itens:
            produto = Produto.query.get(item["produto_id"])
            if not produto or not produto.ativo or produto.estoque < item["quantidade"]:
                return {"erro": f"Produto {item['produto_id']} indisponível ou inexistente"}
            
            preco_item = produto.preco * item["quantidade"]
            total += preco_item
            lista_itens.append(ItemPedido(
                produto_id=item["produto_id"],
                quantidade=item["quantidade"],
                preco_unitario=produto.preco
            ))
            # Decrementar estoque
            produto.estoque -= item["quantidade"]

        # 2. Criar pedido
        novo_pedido = Pedido(usuario_id=usuario_id, total=total, itens=lista_itens)
        db.session.add(novo_pedido)
        db.session.commit()
        
        return {"pedido_id": novo_pedido.id, "total": total}

    @staticmethod
    def get_por_usuario(usuario_id):
        pedidos = Pedido.query.filter_by(usuario_id=usuario_id).all()
        return [p.to_dict() for p in pedidos]

    @staticmethod
    def get_todos():
        pedidos = Pedido.query.all()
        return [p.to_dict() for p in pedidos]

    @staticmethod
    def atualizar_status(pedido_id, novo_status):
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            raise Exception("Pedido não encontrado")
        
        if pedido.status == "cancelado" and novo_status != "cancelado":
            raise Exception("Pedido cancelado não pode ser alterado")
            
        pedido.status = novo_status
        db.session.commit()
        return pedido

    @staticmethod
    def relatorio_vendas():
        # Exemplo simples de logica de relatorio
        pedidos = Pedido.query.all()
        total_vendas = sum(p.total for p in pedidos)
        qtd_pedidos = len(pedidos)
        return {"total_vendas": total_vendas, "qtd_pedidos": qtd_pedidos}
