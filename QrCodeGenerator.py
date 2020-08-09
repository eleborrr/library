import qrcode


def create_qrcode(library_id, book_id):
    img = qrcode.make(f'http://mylibby.ru/{library_id}/{book_id}')
    filename = f'{book_id}.png'
    img.save(filename)


if __name__ == '__main__':
    create_qrcode(1, 2)
