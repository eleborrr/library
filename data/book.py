from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import ForeignKey
from sqlalchemy import orm
import sqlalchemy as sql
import hashlib


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
