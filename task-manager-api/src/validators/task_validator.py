"""Validação de Tarefa — regra única para criação e atualização.

O legado tinha três versões da mesma validação: em `create_task`, em `update_task` (mais
frouxa, sem conversão de tipo de `priority`) e em `utils/helpers.process_task_data`, que nunca
era chamada.
"""
from src.domain.constants import (
    PRIORITY_MAX,
    PRIORITY_MIN,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    VALID_STATUSES,
)
from src.middlewares.error_handler import ValidationError
from src.utils.datetime_utils import parse_date


def _validate_title(valor):
    titulo = str(valor or "").strip()
    if not titulo:
        raise ValidationError("Título é obrigatório")
    if len(titulo) < TITLE_MIN_LENGTH:
        raise ValidationError("Título muito curto")
    if len(titulo) > TITLE_MAX_LENGTH:
        raise ValidationError("Título muito longo")
    return titulo


def _validate_status(valor):
    if valor not in VALID_STATUSES:
        raise ValidationError("Status inválido")
    return valor


def _validate_priority(valor):
    try:
        prioridade = int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}")
    if prioridade < PRIORITY_MIN or prioridade > PRIORITY_MAX:
        raise ValidationError(f"Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}")
    return prioridade


def _validate_due_date(valor, mensagem):
    if valor in (None, ""):
        return None
    data = parse_date(valor)
    if data is None:
        raise ValidationError(mensagem)
    return data


def _validate_optional_id(valor, campo):
    if valor in (None, "", 0):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"{campo} inválido")


def validate_task(dados, partial=False):
    """Normaliza e valida o payload de tarefa.

    `partial=True` (PUT) valida apenas os campos presentes; a regra de cada campo é a mesma
    nos dois modos.
    """
    if not dados:
        raise ValidationError("Dados inválidos")

    saida = {}
    mensagem_data = (
        "Formato de data inválido" if partial else "Formato de data inválido. Use YYYY-MM-DD"
    )

    if not partial or "title" in dados:
        saida["title"] = _validate_title(dados.get("title"))

    if "description" in dados:
        saida["description"] = dados.get("description")
    elif not partial:
        saida["description"] = dados.get("description", "")

    if "status" in dados:
        saida["status"] = _validate_status(dados["status"])

    if "priority" in dados:
        saida["priority"] = _validate_priority(dados["priority"])

    if "user_id" in dados:
        saida["user_id"] = _validate_optional_id(dados["user_id"], "user_id")

    if "category_id" in dados:
        saida["category_id"] = _validate_optional_id(dados["category_id"], "category_id")

    if "due_date" in dados:
        saida["due_date"] = _validate_due_date(dados["due_date"], mensagem_data)

    if "tags" in dados:
        saida["tags"] = dados["tags"]

    return saida


def validate_search_filters(args):
    """Normaliza os filtros de `/tasks/search`, convertendo números com segurança."""

    def _inteiro(campo):
        bruto = args.get(campo)
        if bruto in (None, ""):
            return None
        try:
            return int(bruto)
        except (TypeError, ValueError):
            raise ValidationError(f"{campo} deve ser numérico")

    status = args.get("status") or None
    if status is not None and status not in VALID_STATUSES:
        raise ValidationError("Status inválido")

    return {
        "termo": args.get("q") or None,
        "status": status,
        "priority": _inteiro("priority"),
        "user_id": _inteiro("user_id"),
    }
