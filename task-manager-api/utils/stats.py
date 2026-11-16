def percentage(part, total):
    """Percentual com 2 casas; 0 quando não há total."""
    return round((part / total) * 100, 2) if total > 0 else 0
