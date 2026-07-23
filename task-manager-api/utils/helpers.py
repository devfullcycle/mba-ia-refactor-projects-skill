from datetime import datetime, timezone


def calculate_percentage(part, total):
    if not total:
        return 0
    return round((part / total) * 100, 2)


def parse_date(date_string):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, fmt)
        except (ValueError, TypeError):
            continue
    return None


def is_valid_color(color):
    return bool(color) and len(color) == 7 and color[0] == "#"
