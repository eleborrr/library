from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import orm, ForeignKey
import sqlalchemy as sql


class UserToBook(SqlAlchemyBase):
    __tablename__ = 'user_to_book'
    user_id = Cl(sql.Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    book_id = Cl(sql.Integer, ForeignKey('books.id'), primary_key=True, nullable=False)
