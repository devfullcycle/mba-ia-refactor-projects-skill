import logging

from ..models.admin_model import AdminModel, ConsultaInvalidaError
from .errors import ValidationError

logger = logging.getLogger(__name__)


class AdminController:
    def __init__(self, admin: AdminModel):
        self.admin = admin

    def resetar_banco(self) -> None:
        self.admin.resetar()
        logger.warning("Banco de dados resetado via /admin/reset-db")

    def consultar(self, dados) -> list:
        sql = (dados or {}).get("sql", "") if isinstance(dados, dict) else ""
        if not isinstance(sql, str) or not sql.strip():
            raise ValidationError("Query não informada")
        sql = sql.strip().rstrip(";").strip()
        if not sql.upper().startswith("SELECT") or ";" in sql:
            raise ValidationError("Apenas uma única consulta SELECT é permitida")
        try:
            return self.admin.consultar_somente_leitura(sql)
        except ConsultaInvalidaError as erro:
            logger.info("Consulta admin rejeitada: %s", erro)
            raise ValidationError("Consulta inválida") from None
