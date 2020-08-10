from main import create_roles, lend_book, return_book
from data import db_session, role, user, book, user_to_book, library
import unittest
import os


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(AppTests, cls).setUpClass()
        db_session.global_init('db/tests.sqlite3')

    def test_create_roles(self):
        create_roles()
        session = db_session.create_session()
        roles = {x.name for x in session.query(role.Role).all()}
        self.assertEqual(roles, {'Student', 'Librarian'})
        session.commit()
        session.close()

    def test_lend_book1(self):
        session = db_session.create_session()
        create_roles()
        new_library = library.Library(school_name='school_name')
        session.add(new_library)
        session.commit()
        new_user = user.User(login='login', surname='surname', name='name', password='12345678',
                             library_id=new_library.id,
                             role_id=1)
        session.add(new_user)
        new_book = book.Book(name='name', library_id=new_library.id, author='Author A.A', publication_year=1984, count=1)
        session.add(new_book)
        session.commit()

        lend_book(new_user.id, new_book.id)
        session.commit()

        test_user_to_book = session.query(user_to_book.UserToBook).first()
        first = [test_user_to_book.user_id, test_user_to_book.book_id]
        second = [new_user.id, new_book.id]
        self.assertEqual(first, second, f'{first}/{second}')

        session.close()

    def test_lend_book2(self):
        session = db_session.create_session()
        create_roles()
        new_library = library.Library(school_name='school_name')
        session.add(new_library)
        session.commit()
        new_user = user.User(login='login', surname='surname', name='name', password='12345678',
                             library_id=new_library.id,
                             role_id=1)
        new_user1 = user.User(login='login', surname='surname', name='name', password='12345678',
                             library_id=new_library.id,
                             role_id=1)
        session.add(new_user)
        session.add(new_user1)
        new_book = book.Book(name='name', library_id=new_library.id, author='Author A.A', publication_year=1984,
                             count=1)
        session.add(new_book)
        session.commit()

        lend_book(new_user.id, new_book.id)
        lend_book(new_user1.id, new_book.id)

        test_user_to_book = session.query(user_to_book.UserToBook).all()
        self.assertEqual(len(test_user_to_book), 1)
        session.close()

    def test_lend_book3(self):
        session = db_session.create_session()
        create_roles()
        new_library = library.Library(school_name='school_name')
        session.add(new_library)
        session.commit()
        new_user = user.User(login='login', surname='surname', name='name', password='12345678',
                             library_id=new_library.id,
                             role_id=1)
        new_user1 = user.User(login='login', surname='surname', name='name', password='12345678',
                              library_id=new_library.id,
                              role_id=1)
        session.add(new_user)
        session.add(new_user1)
        new_book = book.Book(name='name', library_id=new_library.id, author='Author A.A', publication_year=1984,
                             count=3)
        session.add(new_book)
        session.commit()

        lend_book(new_user.id, new_book.id)
        lend_book(new_user1.id, new_book.id)

        test_user_to_book = session.query(user_to_book.UserToBook).all()
        self.assertEqual(len(test_user_to_book), 2)
        session.close()

    def test_return_book(self):
        session = db_session.create_session()
        create_roles()
        new_library = library.Library(school_name='school_name')
        session.add(new_library)
        session.commit()
        new_user = user.User(login='login', surname='surname', name='name', password='12345678',
                             library_id=new_library.id,
                             role_id=1)
        new_user1 = user.User(login='login', surname='surname', name='name', password='12345678',
                              library_id=new_library.id,
                              role_id=1)
        session.add(new_user)
        session.add(new_user1)
        new_book = book.Book(name='name', library_id=new_library.id, author='Author A.A', publication_year=1984,
                             count=3)
        session.add(new_book)
        session.commit()

        lend_book(new_user.id, new_book.id)
        lend_book(new_user1.id, new_book.id)

        return_book(new_user.id, new_book.id)
        return_book(new_user1.id, new_book.id)

        self.assertEqual(len(session.query(user_to_book.UserToBook).all()), 0)
        session.close()

    def tearDown(self) -> None:
        session = db_session.create_session()
        for i in ( user_to_book.UserToBook, book.Book, user.User, library.Library, role.Role):
            for j in session.query(i).all():
                session.delete(j)
        session.commit()
        session.close()

    @classmethod
    def tearDownClass(cls) -> None:
        super(AppTests, cls).tearDownClass()
        os.remove('db/tests.sqlite3')


if __name__ == '__main__':
    unittest.main()
