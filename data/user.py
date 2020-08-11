from .db_session import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import orm, ForeignKey
import sqlalchemy as sql
from werkzeug.security import check_password_hash, generate_password_hash


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    login = Cl(sql.String(64), nullable=False, unique=True)
    surname = Cl(sql.String(32), nullable=False)
    name = Cl(sql.String(32), nullable=False)
    password = Cl(sql.String(128), nullable=False)
    class_num = Cl(sql.Integer)
    library_id = Cl(sql.Integer, ForeignKey('libraries.id'))
    library = orm.relation('Library')
    books = orm.relation('Book', back_populates='owner')
    role_id = Cl(sql.Integer, ForeignKey('roles.id'), nullable=False)
    role = orm.relation('Role')

    def __init__(self, *args, **kwargs):
        SqlAlchemyBase.__init__(self, *args, **kwargs)
        self.password = generate_password_hash(self.password)

    def check_password(self, other_passport):
        return check_password_hash(self.password, other_passport)
