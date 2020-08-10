from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import ForeignKey
from sqlalchemy import orm
import sqlalchemy as sql


class Book(SqlAlchemyBase):
    __tablename__ = 'books'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    edition_id = Cl(sql.Integer, ForeignKey('editions.id'), nullable=False)
    edition = orm.relation('Edition')
    owner_id = Cl(sql.Integer, ForeignKey('users.id'))
    owner = orm.relation('User')
