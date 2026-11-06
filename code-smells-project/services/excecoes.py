class AppError(Exception):
    """Erro de negócio/validação com status HTTP; a mensagem é segura para o cliente."""

    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
