import os


class AppConfig:
    SECRET_KEY = 'TestSecretKey'
    SECURITY_PASSWORD_SALT = os.urandom(32)