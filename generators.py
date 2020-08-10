from data import db_session
from data.user import User

import qrcode


def create_qrcode(book_id):
    img = qrcode.make(f'http://mylibby.ru/{book_id}')  # Книга привязана к библиотеке, нет смысла в доп. аргументе
    filename = f'{book_id}.png'
    img.save(filename)


if __name__ == '__main__':
    create_qrcode(1)
