"""Small numeric rules shared by task stats and reports."""


def completion_rate(done, total):
    """Percentage of done tasks, rounded to 2 decimals (0 when there are no tasks)."""
    if total == 0:
        return 0
    return round((done / total) * 100, 2)
