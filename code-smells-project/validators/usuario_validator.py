from exceptions import ValidationError


def _texto_obrigatorio(dados, campo):
    valor = dados.get(campo, "")
    if valor and not isinstance(valor, str):
        raise ValidationError(campo.capitalize() + " inválido")
    return valor


def validar_usuario(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    nome = _texto_obrigatorio(dados, "nome")
    email = _texto_obrigatorio(dados, "email")
    senha = _texto_obrigatorio(dados, "senha")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Email e senha são obrigatórios")

    email = _texto_obrigatorio(dados, "email")
    senha = _texto_obrigatorio(dados, "senha")

    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha
