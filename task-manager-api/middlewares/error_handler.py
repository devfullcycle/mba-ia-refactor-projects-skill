import logging
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'details': str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(SQLAlchemyError)
    def db_error(e):
        logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
