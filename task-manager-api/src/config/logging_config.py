"""Configuração de logging — substitui os 21 `print` de diagnóstico do legado."""
import logging


def configure_logging(app, level="INFO"):
    resolved = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=resolved,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    )
    app.logger.setLevel(resolved)
    return app.logger
