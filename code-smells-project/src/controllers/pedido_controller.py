from src.controllers.usuario_controller import is_admin, verificar_acesso_ao_usuario
from src.models import pedido_model, produto_model, usuario_model
from src.models.pedido_model import EstoqueInsuficienteError, StatusDesatualizadoError, StatusPedido
from src.services import notificacao_service
from src.utils.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from src.utils.validators import is_inteiro

# Ciclo de vida do pedido: estados finais não têm saída.
TRANSICOES_VALIDAS = {
    StatusPedido.PENDENTE: {StatusPedido.APROVADO, StatusPedido.CANCELADO},
    StatusPedido.APROVADO: {StatusPedido.ENVIADO, StatusPedido.CANCELADO},
    StatusPedido.ENVIADO: {StatusPedido.ENTREGUE},
    StatusPedido.ENTREGUE: set(),
    StatusPedido.CANCELADO: set(),
}


def _validar_itens(itens):
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if (
            not isinstance(item, dict)
            or not is_inteiro(item.get("produto_id"))
            or not is_inteiro(item.get("quantidade"))
            or item["quantidade"] <= 0
        ):
            raise ValidationError("Itens devem conter produto_id e quantidade (inteiro positivo)")


def _resolver_usuario_do_pedido(dados, usuario_logado):
    """O pedido é do usuário autenticado; apenas admin pode criar em nome de outro usuário."""
    usuario_id = dados.get("usuario_id", usuario_logado["id"])
    if not is_inteiro(usuario_id):
        raise ValidationError("usuario_id deve ser um número inteiro")
    if usuario_id == usuario_logado["id"]:
        return usuario_id
    if not is_admin(usuario_logado):
        raise ForbiddenError("Não é permitido criar pedidos para outro usuário")
    if usuario_model.buscar_por_id(usuario_id) is None:
        raise ValidationError("Usuário " + str(usuario_id) + " não encontrado")
    return usuario_id


def criar_pedido(dados, usuario_logado):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    usuario_id = _resolver_usuario_do_pedido(dados, usuario_logado)
    itens = dados.get("itens", [])
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
    return {"pedido_id": pedido_id, "usuario_id": usuario_id, "total": total}


def listar_pedidos_usuario(usuario_id, usuario_logado):
    verificar_acesso_ao_usuario(usuario_logado, usuario_id)
    return pedido_model.listar_por_usuario(usuario_id)


def listar_todos_pedidos():
    return pedido_model.listar_todos()


def atualizar_status_pedido(pedido_id, dados):
    valor = dados.get("status", "") if isinstance(dados, dict) else ""
    if valor not in StatusPedido.valores():
        raise ValidationError("Status inválido. Válidos: " + ", ".join(StatusPedido.valores()))
    novo_status = StatusPedido(valor)

    status_atual = pedido_model.buscar_status(pedido_id)
    if status_atual is None:
        raise NotFoundError("Pedido não encontrado")
    status_atual = StatusPedido(status_atual)

    if novo_status not in TRANSICOES_VALIDAS[status_atual]:
        raise ConflictError(f"Transição de status inválida: {status_atual.value} -> {novo_status.value}")

    try:
        pedido_model.atualizar_status(pedido_id, status_atual.value, novo_status.value)
    except StatusDesatualizadoError:
        raise ConflictError("Pedido alterado por outra requisição; tente novamente")

    notificacao_service.notificar_mudanca_status(pedido_id, novo_status)
