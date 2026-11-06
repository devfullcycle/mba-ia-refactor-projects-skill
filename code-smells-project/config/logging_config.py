import logging


def configurar_logging(nivel="INFO"):
    logging.basicConfig(
        level=getattr(logging, nivel, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def mascarar_email(email):
    """Mantém só os 2 primeiros caracteres do usuário e o domínio (ex.: jo***@email.com)."""
    if not isinstance(email, str) or "@" not in email:
        return "***"
    usuario, dominio = email.split("@", 1)
    return usuario[:2] + "***@" + dominio
