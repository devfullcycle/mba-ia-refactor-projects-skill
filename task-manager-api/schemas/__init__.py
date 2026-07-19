def first_error(validation_error):
    """Extrai a primeira mensagem de erro de um ValidationError do marshmallow."""
    for messages in validation_error.messages.values():
        if isinstance(messages, list) and messages:
            return messages[0]
        if isinstance(messages, str):
            return messages
    return 'Dados inválidos'
