from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import orm
import sqlalchemy as sql


class Library(SqlAlchemyBase):
    __tablename__ = 'libraries'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    school_name = Cl(sql.String(64), unique=True, nullable=False)
    users = orm.relation('User', back_populates='library')
    books = orm.relation('Book', back_populates='library')
