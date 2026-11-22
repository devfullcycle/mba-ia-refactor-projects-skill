"""Exceções de domínio convertidas em resposta HTTP pelo tratador central."""


class AppError(Exception):
    """Erro esperado com mensagem segura para o cliente e status HTTP."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status
