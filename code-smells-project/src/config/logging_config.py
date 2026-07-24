"""Configuração de logging — substitui os `print` de diagnóstico do código legado."""
import logging


def configure_logging(app, level="INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    )
    app.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return app.logger
