import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from services.constantes import PERFIL_CLIENTE
from services.excecoes import AppError

_FORMATO_HASH = re.compile(r"^(scrypt|pbkdf2):[^$]+\$[^$]+\$[0-9a-f]+$")


def gerar_hash_senha(senha):
    return generate_password_hash(senha)


class UsuarioService:
    def __init__(self, usuarios):
        self._usuarios = usuarios

    def listar(self):
        return self._usuarios.listar()

    def buscar(self, usuario_id):
        return self._usuarios.buscar_por_id(usuario_id)

    def obter(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise AppError("Usuário não encontrado", 404)
        return usuario

    def criar(self, nome, email, senha):
        if self._usuarios.existe_email(email):
            raise AppError("Email já cadastrado")
        return self._usuarios.criar(nome, email, gerar_hash_senha(senha), PERFIL_CLIENTE)

    def autenticar(self, email, senha):
        for usuario in self._usuarios.buscar_por_email(email):
            if self._senha_confere(usuario, senha):
                return usuario
        return None

    def _senha_confere(self, usuario, senha):
        armazenada = usuario["senha"] or ""
        if _FORMATO_HASH.match(armazenada):
            return check_password_hash(armazenada, senha)
        # Registro legado em texto puro: compara uma única vez e migra para hash.
        if hmac.compare_digest(armazenada.encode(), senha.encode()):
            self._usuarios.atualizar_senha(usuario["id"], gerar_hash_senha(senha))
            return True
        return False
