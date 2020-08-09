from flask import Flask
from data import db_session
from data.book import Book
from data.library import Library
from data.user import User
from data.role import Role

app = Flask(__name__)


@app.before_first_request
def create_roles():
    session = db_session.create_session()
    roles = {'Student', 'Librarian'}
    for i in session.query(Role).all():
        roles.discard(i.name)
    for i in roles:
        role = Role()
        role.name = i
        session.add(role)
    session.commit()


if __name__ == '__main__':
    db_session.global_init('db/library.sqlite3')
    app.run()

