from data import db_session
from data.user import User

import qrcode
import random


def create_qrcode(library_id, book_id):
    img = qrcode.make(f'http://mylibby.ru/{library_id}/{book_id}')
    filename = f'{book_id}.png'
    img.save(filename)


def generate_login():
    chars = '+-!?=abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    digits_for_login = '1234567890'
    password_login_length = 8
    password = ''
    login = ''
    for i in range(password_login_length):
        password += random.choice(chars)
    session = db_session.create_session()
    logins = session.query(User).filter(User.login).all()
    while login in logins:
        login = ''
        for i in range(password_login_length):
            login += random.choice(digits_for_login)
    return login, password


if __name__ == '__main__':
    create_qrcode(1, 2)
