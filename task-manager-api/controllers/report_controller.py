from flask import jsonify

from models.user import User
from services import report_service
from middlewares.error_handler import ApiError


def summary_report():
    return jsonify(report_service.build_summary()), 200


def user_report(user_id):
    user = User.get(user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)
    return jsonify(report_service.build_user_report(user)), 200
