from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import os
import qrcode
import io
import base64


def _create_qrcode(book_code, id_):
    img = qrcode.make(f'http://9da87d86f199.ngrok.io/borrow_book/{book_code}')
    img = img.resize((165, 165))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('static/fonts/qr_font.ttf', 16)
    msg = f'#{id_}'
    w, h = draw.textsize(msg, font)
    draw.text(xy=((165 - w) / 2, 150), text=msg, fill=(0,), font=font)
    return img


# def create_qrcode(book_id):
#     _create_qrcode(book_id).save(f'{book_id}.png')


def _create_qr_list(ids):
    res = []
    res1 = []
    for i in range((len(ids) + 14) // 15):
        cur = Image.new('RGB', (594, 846), 'white')
        for x in range(5):
            for y in range(3):
                try:
                    book_id = ids[i * 15 + x * 3 + y]
                except IndexError:
                    break
                offset = 165 * y, 165 * x
                cur.paste(_create_qrcode(*book_id), offset)
        cur_res = io.BytesIO()
        cur.save(cur_res, format='JPEG')
        x = base64.b64encode(cur_res.getvalue()).decode('utf-8')
        print(x)
        res.append(x)
        res1.append(cur)
    return res, res1


def create_qrcode(book_code, id_):
    img = _create_qrcode(book_code, id_)
    cur_res = io.BytesIO()
    img.save(cur_res, format='JPEG')
    x = base64.b64encode(cur_res.getvalue()).decode('utf-8')
    return x


# def create_qr_list(ids):
#     try:
#         os.mkdir('qr_lists')
#     except FileExistsError:
#         pass
#     i = 1
#     for img in _create_qr_list(ids)[1]:
#         img.save(f'qr_lists/{i}.png')
#         i += 1


if __name__ == '__main__':
    pass
    # create_qr_list(list(range(1, 21)))
