from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import ForeignKey
from sqlalchemy import orm
import sqlalchemy as sql
import hashlib
from flask import Markup


class Book(SqlAlchemyBase):
    __tablename__ = 'books'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    edition_id = Cl(sql.Integer, ForeignKey('editions.id'), nullable=False)
    edition = orm.relation('Edition')
    owner_id = Cl(sql.Integer, ForeignKey('users.id'))
    owner = orm.relation('User')

    def generate_id(self):
        return hashlib.shake_128(b'book' + str(self.id).encode()).hexdigest(16)

    def check_id(self, other):
        return other == self.generate_id()

    def render(self, is_librarian):
        lib_content = f'''<a href="/library/delete_book/{self.generate_id()}">Удалить книгу из библиотеки</a><br>
<a href="/library/give_book/{self.generate_id()}">Выдать книгу</a>''' if not self.owner \
            else f'<a href="/library/return_book/{self.generate_id()}">Вернуть книгу</a>'
        html = f"""<p>id:{self.id}</p><br>
<p>Текущий владелец: {"Книга в библиотеке" if self.owner else self.owner.surname + ' ' + self.owner.name}</p><br>
<p>Информация об издании:</p><br>
<div>
    <p>Название книги: {self.edition.name}</p><br>
    <p>Автор: {self.edition.author}</p><br>
    <p>Год публикации: {self.edition.publication_year}</p><br>
</div>
<div>
    <a href="/library/book/{self.id}">Открыть информацию о книге</a><br>
    {lib_content if is_librarian else ''}
</div>
"""
        return Markup(html)