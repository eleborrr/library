from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import ForeignKey
from sqlalchemy import orm
import sqlalchemy as sql


class Book(SqlAlchemyBase):
    __tablename__ = 'books'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = Cl(sql.String(64), nullable=False)
    author = Cl(sql.String(64), nullable=False)
    publication_year = Cl(sql.Integer)
    library_id = Cl(sql.Integer, ForeignKey('libraries.id'), nullable=False)
    library = orm.relation('Library')
    count = Cl(sql.Integer)
    owners = orm.relation('User', secondary='user_to_book')
