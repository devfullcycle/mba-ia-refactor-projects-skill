from flask import current_app


def get_controller(name):
    return current_app.extensions["controllers"][name]
