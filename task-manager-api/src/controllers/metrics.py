def completion_rate(done, total):
    """Percentage of done tasks, rounded to 2 decimals (0 when there are no tasks)."""
    return round((done / total) * 100, 2) if total > 0 else 0
