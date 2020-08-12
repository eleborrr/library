from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import orm
import sqlalchemy as sql
import hashlib


class Library(SqlAlchemyBase):
    __tablename__ = 'libraries'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    school_name = Cl(sql.String(64), nullable=False)
    users = orm.relation('User', back_populates='library')
    editions = orm.relation('Edition', back_populates='library')

    def generate_id(self):
        return hashlib.shake_128(str(self.id).encode()).hexdigest(8)

    def check_id(self, other):
        return hashlib.shake_128(other.encode()).hexdigest(8) == self.generate_id()
