from flask import jsonify

from middlewares.auth import current_user
from services import access_policy, report_service
from views import report_view


def summary_report():
    return jsonify(report_view.render_summary(report_service.summary())), 200


def user_report(user_id):
    access_policy.ensure_can_view_user_report(current_user(), user_id)
    return jsonify(report_view.render_user_report(report_service.user_report(user_id))), 200
