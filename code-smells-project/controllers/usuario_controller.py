from flask import request, jsonify
from services.usuario_service import UsuarioService

def listar_usuarios():
    try:
        usuarios = UsuarioService.listar_usuarios()
        return jsonify({"dados": usuarios, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def buscar_usuario(id):
    try:
        usuario = UsuarioService.buscar_usuario(id)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def criar_usuario():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        id = UsuarioService.criar_usuario(dados.get("nome", ""), dados.get("email", ""), dados.get("senha", ""))
        return jsonify({"dados": {"id": id}, "sucesso": True}), 201

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def login():
    try:
        dados = request.get_json()
        usuario = UsuarioService.login(dados.get("email", ""), dados.get("senha", ""))
        
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
        else:
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
