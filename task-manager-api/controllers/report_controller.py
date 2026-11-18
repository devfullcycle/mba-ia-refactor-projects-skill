from flask import jsonify

from services import report_service


def summary_report():
    return jsonify(report_service.summary()), 200


def user_report(user_id):
    return jsonify(report_service.user_report(user_id)), 200
