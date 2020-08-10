from flask import Flask
from data import db_session
from data.book import Book
from data.library import Library
from data.user import User
from data.role import Role
from data.user_to_book import UserToBook

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
    session.close()


def lend_book(user_id, book_id):
    session = db_session.create_session()
    user: User = session.query(User).get(user_id)
    book: Book = session.query(Book).get(book_id)
    if book.count > len(book.owners):
        user.books.append(book)
    session.commit()
    session.close()


def return_book(user_id, book_id):
    session = db_session.create_session()
    try:
        session.delete(session.query(UserToBook).filter(UserToBook.user_id == user_id,
                                                        UserToBook.book_id == book_id).first())
    except Exception:
        pass
    session.commit()
    session.close()


if __name__ == '__main__':
    db_session.global_init('db/library.sqlite3')
    app.run()

