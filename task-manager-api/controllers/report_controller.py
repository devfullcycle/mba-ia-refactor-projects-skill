from services import report_service


def summary():
    return report_service.summary(), 200


def user_report(user_id):
    return report_service.user_report(user_id), 200
