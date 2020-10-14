import os

from flask import url_for


class AppConfig:
    SECRET_KEY = 'TestSecretKey'
    SECURITY_PASSWORD_SALT = os.urandom(32)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USE_TLS = True
    MAIL_PORT = 587
    MAIL_USERNAME = 'testing.some.web.apps@gmail.com'  # Я серьёзно создал эту почту, можете пользоваться
    MAIL_PASSWORD = 'TestIsCool1'
    MAIL_DEFAULT_SENDER = 'TestSender'
    UPLOAD_FOLDER = '/static/img/editions/'
