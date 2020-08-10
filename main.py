from flask import Flask
from data import db_session
from data.book import Book
from data.edition import Edition
from data.library import Library
from data.user import User
from data.role import Role
from config import AppConfig

app = Flask(__name__)
app.config.from_object(AppConfig)


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
    session.close()


def create_library(school_name, **librarian_data):  # login, name, surname, password
    session = db_session.create_session()
    lib = Library(school_name=school_name)
    session.add(lib)
    session.commit()
    session.add(User(**librarian_data, role_id=2, library_id=lib.id,
                     class_num=None))
    session.commit()
    session.close()


def add_edition(library_id, count, **edition_data):  # name, author, publication_year
    session = db_session.create_session()
    edition = Edition(**edition_data, library_id=library_id)
    session.add(edition)
    session.commit()
    for i in range(count):
        session.add(Book(edition_id=edition.id))
    session.commit()


def add_book(edition_id):
    session = db_session.create_session()
    session.add(Book(edition_id=edition_id))
    session.commit()
    session.close()


def remove_book(book_id):
    session = db_session.create_session()
    session.delete(session.query(Book).get(book_id))
    session.commit()
    session.close()


def lend_book(user_id, book_id):
    session = db_session.create_session()
    book = session.query(Book).get(book_id)
    if not book.owner:
        book.owner_id = user_id
    session.commit()
    session.close()


def return_book(book_id):
    session = db_session.create_session()
    book = session.query(Book).get(book_id)
    book.owner_id = None
    session.commit()
    session.close()


def register_student(name, surname, login, password, library_id, class_num):
    session = db_session.create_session()
    ex_user = session.query(User).filter(User.login == login).first()
    if not ex_user:
        session.add(User(name=name, surname=surname, password=password, role_id=1, library_id=library_id,
                         class_num=class_num, login=login))
    session.commit()
    session.close()


if __name__ == '__main__':
    db_session.global_init('db/library.sqlite3')
    app.run()

