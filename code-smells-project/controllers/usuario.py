from flask import jsonify
from models import usuario
from utils.validators import validar_usuario
from utils.logger import get_logger

logger = get_logger(__name__)

def listar():
    try:
        usuarios_list = usuario.listar_todos()
        return jsonify({"dados": usuarios_list, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        return jsonify({"erro": "Erro ao listar usuários"}), 500

def buscar_por_id(id):
    try:
        usu = usuario.buscar_por_id(id)
        if usu:
            return jsonify({"dados": usu, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {str(e)}")
        return jsonify({"erro": "Erro ao buscar usuário"}), 500

def criar(dados):
    try:
        erros = validar_usuario(dados)
        if erros:
            return jsonify({"erros": erros}), 400

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        id = usuario.criar(nome, email, senha)
        logger.info(f"Usuário criado: {email}")
        return jsonify({"dados": {"id": id}, "sucesso": True}), 201

    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        return jsonify({"erro": "Erro ao criar usuário"}), 500

def autenticar(dados):
    try:
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usu = usuario.autenticar(email, senha)
        if usu:
            logger.info(f"Login bem-sucedido: {email}")
            return jsonify({"dados": usu, "sucesso": True, "mensagem": "Login OK"}), 200
        else:
            logger.info(f"Login falhou: {email}")
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401

    except Exception as e:
        logger.error(f"Erro ao autenticar: {str(e)}")
        return jsonify({"erro": "Erro ao autenticar"}), 500
