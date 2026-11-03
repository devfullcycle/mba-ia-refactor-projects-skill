from src.models import pedido_model, produto_model
from src.models.pedido_model import EstoqueInsuficienteError
from src.services import notificacao_service
from src.utils.errors import NotFoundError, ValidationError

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def _is_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_itens(itens):
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if (
            not isinstance(item, dict)
            or not _is_inteiro(item.get("produto_id"))
            or not _is_inteiro(item.get("quantidade"))
            or item["quantidade"] <= 0
        ):
            raise ValidationError("Itens devem conter produto_id e quantidade (inteiro positivo)")


def criar_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    _validar_itens(itens)

    produtos = produto_model.buscar_por_ids({item["produto_id"] for item in itens})

    total = 0
    itens_pedido = []
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError("Estoque insuficiente para " + produto["nome"])
        total = total + (produto["preco"] * item["quantidade"])
        itens_pedido.append({**item, "preco_unitario": produto["preco"]})

    try:
        pedido_id = pedido_model.criar(usuario_id, itens_pedido, total)
    except EstoqueInsuficienteError as exc:
        # Estoque consumido por outro pedido entre a validação e a baixa (ou item repetido no pedido).
        raise ValidationError("Estoque insuficiente para " + produtos[exc.produto_id]["nome"])

    notificacao_service.notificar_pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_pedidos_usuario(usuario_id):
    return pedido_model.listar_por_usuario(usuario_id)


def listar_todos_pedidos():
    return pedido_model.listar_todos()


def atualizar_status_pedido(pedido_id, dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    if not pedido_model.existe(pedido_id):
        raise NotFoundError("Pedido não encontrado")

    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.notificar_mudanca_status(pedido_id, novo_status)
