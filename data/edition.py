from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import ForeignKey
from sqlalchemy import orm
import sqlalchemy as sql


class Edition(SqlAlchemyBase):
    __tablename__ = 'editions'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = Cl(sql.String(64), nullable=False)
    author = Cl(sql.String(64), nullable=False)
    publication_year = Cl(sql.Integer, nullable=False)
    avatar_image = Cl(sql.String(64), default='none.jpg')
    library_id = Cl(sql.Integer, ForeignKey('libraries.id', ondelete='CASCADE'), nullable=False)
    library = orm.relation('Library')
    books = orm.relation('Book', back_populates='edition')
    ed_name = Cl(sql.String(64), nullable=False) # publisher name
    class_num = Cl(sql.Integer)
    # category = None  # Новая модель или строка??????????????

