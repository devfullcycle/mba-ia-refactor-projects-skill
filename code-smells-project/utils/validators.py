from config import settings

def validar_produto(dados, obrigatorio_completo=True):
    erros = []

    if not dados:
        erros.append("Dados inválidos")
        return erros

    if obrigatorio_completo or "nome" in dados:
        nome = dados.get("nome", "")
        if not nome:
            erros.append("Nome é obrigatório")
        elif len(nome) < 2:
            erros.append("Nome muito curto")
        elif len(nome) > 200:
            erros.append("Nome muito longo")

    if obrigatorio_completo or "preco" in dados:
        preco = dados.get("preco")
        if preco is None:
            erros.append("Preço é obrigatório")
        elif preco < 0:
            erros.append("Preço não pode ser negativo")

    if obrigatorio_completo or "estoque" in dados:
        estoque = dados.get("estoque")
        if estoque is None:
            erros.append("Estoque é obrigatório")
        elif estoque < 0:
            erros.append("Estoque não pode ser negativo")

    if "categoria" in dados:
        categoria = dados.get("categoria", "geral")
        if categoria not in settings.CATEGORIAS_VALIDAS:
            erros.append(f"Categoria inválida. Válidas: {', '.join(settings.CATEGORIAS_VALIDAS)}")

    return erros

def validar_usuario(dados):
    erros = []

    if not dados:
        erros.append("Dados inválidos")
        return erros

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        erros.append("Nome, email e senha são obrigatórios")

    return erros

def validar_status_pedido(status):
    if status not in settings.STATUSES_VALIDOS:
        return [f"Status inválido. Válidos: {', '.join(settings.STATUSES_VALIDOS)}"]
    return []
