from main import create_roles, lend_book, return_book, register_student, create_library, add_edition, add_book, remove_book
from data import db_session, role, user, edition, library, book
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

    def test_register_student(self):
        create_roles()
        session = db_session.create_session()
        lib = library.Library(school_name='1')
        session.add(lib)
        session.commit()
        register_student('name', 'surname', 'login', 'password', lib.id, 7)
        register_student('name', 'surname', 'login', 'password', lib.id, 7)
        self.assertEqual(len(session.query(user.User).all()), 1)
        session.close()

    def test_create_library(self):
        create_library('School Name',
                       login='login',
                       name='name',
                       surname='surname',
                       password='password')
        session = db_session.create_session()
        librarian = session.query(user.User).first()
        self.assertIsNotNone(librarian)
        self.assertEqual(librarian.role_id, 2)
        self.assertEqual(librarian.library_id, 1)
        self.assertIsNotNone(session.query(library.Library).first())
        session.close()

    def test_add_edition(self):
        create_library('School Name',
                       login='login',
                       name='name',
                       surname='surname',
                       password='password')
        session = db_session.create_session()
        lib = session.query(library.Library).first()
        add_edition(lib.id, 4,
                    name='name',
                    author='author',
                    publication_year=1984)
        ed = session.query(edition.Edition).first()
        self.assertIsNotNone(ed)
        books = session.query(book.Book).all()
        self.assertEqual(len(books), 4)
        for i in books:
            self.assertEqual(i.edition_id, ed.id)
        session.close()

    def test_lend_book(self):
        create_library('School Name',
                       login='login',
                       name='name',
                       surname='surname',
                       password='password')
        session = db_session.create_session()
        lib = session.query(library.Library).first()
        add_edition(lib.id, 4,
                    name='name',
                    author='author',
                    publication_year=1984)
        register_student('name', 'surname', 'login', 'password', lib.id, 7)
        register_student('name', 'surname', 'login1', 'password', lib.id, 7)
        user1 = session.query(user.User).get(1)
        user2 = session.query(user.User).get(2)
        self.assertIsNotNone(user1)
        self.assertIsNotNone(user2)
        lend_book(user1.id, 1)
        lend_book(user2.id, 3)
        book1 = session.query(book.Book).get(1)
        book2 = session.query(book.Book).get(2)
        book3 = session.query(book.Book).get(3)
        book4 = session.query(book.Book).get(4)
        self.assertIsNotNone(book1)
        self.assertIsNotNone(book2)
        self.assertIsNotNone(book3)
        self.assertIsNotNone(book4)
        self.assertEqual(book1.owner_id, user1.id, 1)
        self.assertEqual(book2.owner_id, None, 2)
        self.assertEqual(book3.owner_id, user2.id, 3)
        self.assertEqual(book4.owner_id, None, 4)
        session.close()

    def test_return_book(self):
        create_library('School Name',
                       login='login',
                       name='name',
                       surname='surname',
                       password='password')
        session = db_session.create_session()
        lib = session.query(library.Library).first()
        add_edition(lib.id, 4,
                    name='name',
                    author='author',
                    publication_year=1984)
        register_student('name', 'surname', 'login', 'password', lib.id, 7)
        register_student('name', 'surname', 'login1', 'password', lib.id, 7)
        user1 = session.query(user.User).get(1)
        user2 = session.query(user.User).get(2)
        lend_book(user1.id, 1)
        lend_book(user2.id, 3)
        for i in range(1, 5):
            return_book(i)
        for i in session.query(book.Book).all():
            self.assertIsNone(i.owner_id)
        session.close()

    def test_add_book(self):
        create_library('School Name',
                       login='login',
                       name='name',
                       surname='surname',
                       password='password')
        session = db_session.create_session()
        lib = session.query(library.Library).first()
        add_edition(lib.id, 4,
                    name='name',
                    author='author',
                    publication_year=1984)
        ed = session.query(edition.Edition).first()

        add_book(ed.id)

        new_book = session.query(book.Book).get(5)
        self.assertIsNotNone(new_book)
        self.assertEqual(new_book.edition_id, ed.id)
        session.close()

    def test_remove_book(self):
        create_library('School Name',
                       login='login',
                       name='name',
                       surname='surname',
                       password='password')
        session = db_session.create_session()
        lib = session.query(library.Library).first()
        add_edition(lib.id, 4,
                    name='name',
                    author='author',
                    publication_year=1984)

        remove_book(2)
        self.assertEqual(len(session.query(book.Book).all()), 3)
        session.close()


    def tearDown(self) -> None:
        session = db_session.create_session()
        for i in (book.Book, edition.Edition, library.Library, role.Role, user.User):
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
