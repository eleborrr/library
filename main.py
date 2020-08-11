from flask import Flask, redirect, render_template
from data import db_session
from data.book import Book
from data.edition import Edition
from data.library import Library
from data.user import User
from data.role import Role
from config import AppConfig
from generators import create_qr_list
from flask_login import LoginManager, logout_user, login_user, login_required, current_user
from flask_classy import route, FlaskView
from forms import *

app = Flask(__name__)
login_manager = LoginManager(app)
app.config.from_object(AppConfig)


def create_library(school_name, **librarian_data):  # login, name, surname, password
    session = db_session.create_session()
    lib = Library(school_name=school_name)
    session.add(lib)
    session.commit()
    role_id = session.query(Role).filter(Role.name == 'Librarian').first().id
    session.add(User(**librarian_data, role_id=role_id, library_id=lib.id,
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
    role_id = session.query(Role).filter(Role.name == 'Candidate').first().id
    if not ex_user:
        us = User(name=name, surname=surname, password=password, role_id=role_id, library_id=library_id,
                         class_num=class_num, login=login)
        session.add(us)
        login_user(us)
    session.commit()
    session.close()


def bind_student(user_id):
    session = db_session.create_session()
    session.query(User).get(user_id).role_id = session.query(Role).filter(Role.name == 'Student').id
    session.commit()
    session.close()


def generate_edition_qr(edition_id):
    session = db_session.create_session()
    create_qr_list([x.id for x in session.query(Edition).get(edition_id).books])


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    try:
        return session.query(User).get(user_id)
    finally:
        session.close()


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.before_first_request
def create_roles():
    session = db_session.create_session()
    roles = {'Student', 'Librarian', 'Candidate'}
    for i in session.query(Role).all():
        roles.discard(i.name)
    for i in roles:
        role = Role()
        role.name = i
        session.add(role)
    session.commit()
    session.close()


@app.route('/create_library')
def register_library():
    form = CreateLibraryForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        ex = session.query(User).filter(User.login == form.email.data).first()
        if ex:
            pass  # Если почта использована
        if form.password.data != form.repeat.data:
            pass  # Если пароли не совпадают
        create_library(form.library_school_name.data,
                       login=form.email.data,
                       name=form.name.data,
                       surname=form.surname.data,
                       password=form.password.data)
        return redirect('/library')
    session.close()
    return render_template('create_library.jinja2', form=form)


@app.route('/register_student')
def create_student():
    form = RegisterStudentForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        ex = session.query(User).filter(User.login == form.email.data).first()
        if ex:
            pass  # Если почта использована
        if form.password.data != form.repeat.data:
            pass  # Если пароли не совпадают
        if not session.query(Library).get(form.library_id.data):
            pass  # Если задан неправильный номер библиотеки
        register_student(form.name.data, form.surname.data, form.email.data, form.password.data, form.library_id.data,
                         form.class_num.data)
        return redirect('/library')
    session.close()
    return render_template('register_student.jinja2', form=form)


@app.route('/login')
def login():
    form = LoginForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        us: User = session.query(User).filter(User.login == form.email.data).first()
        if not us:
            pass  # Если такой адрес не зарегестрирован
        if not us.check_password(form.password.data):
            pass  # Если введён неверный пароль
        login_user(us, remember=form.remember_me.data)
        return redirect('/library')
    return render_template('login.jinja2', form=form)


class LibraryView(FlaskView):
    @route('/')
    @login_required
    def index(self):
        # Я решил не делать /<int:library_id>, потому что человек не сможет посмотреть какую-либо библиотеку,
        # кроме своей
        # Мы просто определим его библиотеку и покажем её без доп. аргументов
        session = db_session.create_session()
        library = session.query(Library).get(current_user.library_id)
        #  Что здесь будет:
        #  Если user имеет роль "Candidate", на странице будет написано
        #  Вы подали заявку в библиотеку #{id библиотеки}
        #  Дождитесь когда заявка будет принята
        #  Под надписью будет маленькая ссылка:
        #  Ошиблись библиотекой? <a href="ещё не придумал">Сменить номер библиотеки</a>

        #  Если user имеет роль "Student", на сайте будет написано
        #  Вы причислены к библиотек #{id библиотеки}
        #  Под надписью будет маленькая ссылка:
        #  Ошиблись библиотекой? <a href="ещё не придумал">Сменить номер библиотеки</a>
        #  (Здесь ссылка на случай, если библиотекарь по ошибке принял чужого ребенка)
        #  Под этой подписью список всех книг, которые он взял (с поиском)

        #  Если user - "Librarian", на сайте будет написано
        #  Вы управляете библиотекой #{id библиотеки}
        #  (Регистрация устроена так, что ошибиться с номером библиотеки не получится)
        #  Ниже будет список всех книг, которые взяли из библиотеки (с поиском)
        #  Рядом с каждой книгой кнопка "Вернуть в библиотеку"

        #  У каждого есть возможность изменить свой профиль
        #  А у библиотекаря так же имя школы

        #  Под списком книг понимается список ссылкок на library/books/{book_id}

    @route('/editions')
    @login_required
    def editions(self):
        session = db_session.create_session()
        library = session.query(Library).get(current_user.library_id)
        candidate_role = session.query(Role).filter(Role.name == 'Candidate').first()
        if current_user.role_id == candidate_role:
            pass  # Те, чью заявку не приняли, не допускаются
        #  Эта вкладка доступна всем членам библиотеки
        #  Здесь будет находиться список всех изданий (editions)
        #  Под списком изданий понимается список ссылок на library/edition/{edition_id}
        #  У библиотекаря должна быть кнопка "Добавить книгу" (не "Добавить издание", слишком непонятно),
        #  добавляющее новое издание

    @route('/editions/<int:edition_id>')
    @login_required
    def edition(self, edition_id):
        session = db_session.create_session()
        library = session.query(Library).get(current_user.library_id)
        edition = session.query(Edition).get(edition_id)
        candidate_role = session.query(Role).filter(Role.name == 'Candidate').first()
        if current_user.role_id == candidate_role:
            pass  # Те, чью заявку не приняли, не допускаются
        if not edition:
            pass  # Такого издания не существует
        if edition.library_id != library.id:
            pass  # Если это издание не принадлежит этой библиотеке
            #  Стоит отметить, что хоть одна и таже книга (одно и тоже издание) может быть в нескольких библиотеках,
            #  Каждое издание привязано к конкретной библиотеке
        # Сдесь будет список книг данного издания с их текущими владельцами
        # У библиотекаря рядом с каждой книгой есть кнопка "Вернуть в библиотеку" или "Одолжить книгу"
        # (Я думаю у библиотекаря должна быть возможность одалживать книгу вручную),
        # А так эе кнопка "Удалить" (Вдруг случайно лишнюю создала") P.s кнопка недоступна, если книга не в библиотеке
        # Так же библиотекарю доступна кнопка "Добавить книгу", добавляющая новую книгу этого издания,
        # и кнопка "список qr-кодов"

    @route('/books/<int:book_id>')
    @login_required
    def book(self, book_id):
        session = db_session.create_session()
        library = session.query(Library).get(current_user.library_id)
        book = session.query(Book).get(book_id)
        if not book:
            pass  # Такой книги не существует
        if book.edition.library_id != library.id:
            pass  # Если это издание не принадлежит этой библиотеке
        candidate_role = session.query(Role).filter(Role.name == 'Candidate').first()
        if current_user.role_id == candidate_role:
            pass  # Те, чью заявку не приняли, не допускаются
        #  Здесь будут находиться
        #  id книги (именно книги, не издания)
        #  Информация об ИЗДАНИИ (тип название, автор, год издания и тд.)
        #  У библиотекаря есть такие же кнопки, как и рядом с каждой книгой в списке,
        #  А так же кнопка "Получить qr-код"

    @route('/students')
    @login_required
    def students(self):
        session = db_session.create_session()
        library = session.query(Library).get(current_user.library_id)
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        if current_user.role_id != librarian_role.id:
            pass  # Эта вкладка доступна только библиотекарю
        # Здесь будет находиться список всех учащихся, привязанных к данной библиотеке
        # Список учащихся - спичок ссылок на library/students/{student_id}

    @route('/students/<int:user_id>')
    @login_required
    def student(self, user_id):
        session = db_session.create_session()
        library = session.query(Library).get(current_user.library_id)
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        if current_user.role_id != librarian_role.id:
            pass  # Эта вкладка доступна только библиотекарю
        student = session.query(User).get(user_id)
        if not student:
            pass  # Если такого юзера не существует
        student_role = session.query(Role).filter(Role.name == 'Student').first()
        if student.role_id != student_role.id:
            pass  # В этой вкладке должен быть ученик, привязанный к библиотеке

        #  Здесь библиотекарь видит Фамилию и Имя ученика
        #  И список всех книг, которые у него сейчас находятся
        #  P.S. это не профиль студента (я думаю, профили других людей будут недоступны)

    @route('/candidates')
    @login_required
    def candidates(self):
        session = db_session.create_session()
        library = session.query(Library).get(current_user.library_id)
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        if current_user.role_id != librarian_role.id:
            pass  # Эта вкладка доступна только библиотекарю
        # Здесь будут все юзеры с ролью candidate, привязанные к данной библиотеке
        # Рядом с каждым юзером будет кнопка "Принять заявку"
        # Нажав на неё, роль юзера меняется на student


if __name__ == '__main__':
    db_session.global_init('db/library.sqlite3')
    app.run()

