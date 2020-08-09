from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import orm, ForeignKey
import sqlalchemy as sql


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    surname = Cl(sql.String(32), nullable=False)
    name = Cl(sql.String(32), nullable=False)
    library_id = Cl(sql.Integer, ForeignKey('libraries.id'))
    library = orm.relation('Library')
    books = orm.relation('Book', back_populates='owner')
    role_id = Cl(sql.Integer, ForeignKey('role.id'), nullable=False)
    role = orm.relation('Role')
