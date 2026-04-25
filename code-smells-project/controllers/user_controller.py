import models.user_model as user_model


def list_all():
    usuarios = user_model.get_all()
    return ({"dados": usuarios, "sucesso": True}, 200)


def get_by_id(user_id):
    usuario = user_model.get_by_id(user_id)
    if usuario:
        return ({"dados": usuario, "sucesso": True}, 200)
    return ({"erro": "Usuario nao encontrado", "sucesso": False}, 404)


def create(dados):
    if not dados:
        return ({"erro": "Dados invalidos"}, 400)

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return ({"erro": "Nome, email e senha sao obrigatorios"}, 400)

    user_id = user_model.create(nome, email, senha)
    return ({"dados": {"id": user_id}, "sucesso": True}, 201)


def login(dados):
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return ({"erro": "Email e senha sao obrigatorios"}, 400)

    usuario = user_model.authenticate(email, senha)
    if usuario:
        return ({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200)
    return ({"erro": "Email ou senha invalidos", "sucesso": False}, 401)
