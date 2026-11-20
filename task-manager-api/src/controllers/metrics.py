"""Small business metrics reused by several controllers."""

PERCENT_DECIMALS = 2


def completion_rate(completed, total):
    return round((completed / total) * 100, PERCENT_DECIMALS) if total > 0 else 0
