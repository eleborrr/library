from flask import Flask, redirect, render_template, abort, request
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
    user = User(**librarian_data, role_id=role_id, library_id=lib.id,
                class_num=None)
    session.add(user)
    login_user(user)
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


# @app.errorhandler(401)
# def error_401(er):
#     return redirect('/sign_in#tab_03'), 401
#
#
# @app.errorhandler(403)
# def error_403(er):
#     return render_template('тебе_сюда_нельзя.html', msg=er.message), 403
#
#
@app.errorhandler(404)
def error_404(er):
    if er.description == 'The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.':
        er.description = 'Страница не найдена'
    return render_template('404.html', msg=er.description), 404

#
# @app.errorhandler(500)
# def error_500(er):
#     return render_template('разрабы_тупые_криворученки.html', msg=er.message), 404


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
    roles = {'Student', 'Librarian'}
    for i in session.query(Role).all():
        roles.discard(i.name)
    for i in roles:
        role = Role()
        role.name = i
        session.add(role)
    # print(session.query(Library).get(1).generate_id())
    session.commit()
    session.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if current_user.is_authenticated:
        return redirect('/library')
    session = db_session.create_session()
    library_form = CreateLibraryForm()
    login_form = LoginForm()
    register_form = RegisterStudentForm()
    if library_form.validate_on_submit():
        ex = session.query(User).filter(User.login == library_form.email.data).first()
        if ex:
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=1, msg1="Этот адрес электронной почты уже занят")
        if library_form.password.data != library_form.repeat.data:
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=1, msg1="Пароли не совпадают")
        if '_' in library_form.name.data:
            # обработать и другие символы
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=1, msg1="Недопустимые символы в названии библиотеки")
        create_library(library_form.library_school_name.data,
                       login=library_form.email.data,
                       name=library_form.name.data,
                       surname=library_form.surname.data,
                       password=library_form.password.data)
        return redirect('/library')
    if login_form.validate_on_submit():
        us = session.query(User).filter(User.login == login_form.email.data).first()
        if not us:
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=3, msg3="Неверный адрес электронной почты")
        if not us.check_password(login_form.password.data):
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=3, msg3="Неверный пароль")
        login_user(us, remember=login_form.remember_me.data)
        return redirect('/library')
    if register_form.validate_on_submit():
        ex = session.query(User).filter(User.login == register_form.email.data).first()
        if ex:
            render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                            login_form=login_form, tab_num=2, msg2="Этот адрес электронной почты уже занят")
        if register_form.password.data != register_form.repeat.data:
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=2, msg2="Пароли не совпадают")
        if '_' in register_form.name.data or '_' in register_form.surname.data:
            # обработать и другие символы
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=2, msg2="Недопустимые символы в имени пользователя")
        for i in session.query(Library).all():
            if i.check_id(register_form.library_id.data):
                lib_id = i.id
                break
        else:
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=2, msg2="Неверный идентификатор библиотеки")
        register_student(register_form.name.data, register_form.surname.data, register_form.email.data,
                         register_form.password.data, lib_id,
                         register_form.class_num.data)
        return redirect('/library')
    return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                           login_form=login_form, tab_num=3)


@app.route('/borrow_book/<string:code>')
def borrow_book(code):
    session = db_session.create_session()
    for i in session.query(Book).all():
        if i.check_id(code):
            cur_book = i
            break
    else:
        return abort(404, description='Неверный идентификатор книги')  # Шаблон с сообщением в центре экрана
    if not cur_book.owner:
        form = BorrowBookForm()
        if form.validate_on_submit() and current_user.is_authenticated:
            if current_user.library_id == cur_book.edition.library_id:
                cur_book.owner_id = current_user.id
                session.commit()
                session.close()
                return render_template('message.html', msg='Книга добавлена в ваш формуляр')
            else:
                return render_template('message.html',
                                       msg='Эта книга принадлежит другой библиотеке!')  # отнеси ее туда, не будь говнюком
        elif form.validate_on_submit() and not current_user.is_authenticated:
            login_form = LoginForm()
            if login_form.validate_on_submit():
                us = session.query(User).filter(User.login == login_form.email.data).first()
                if not us:
                    return render_template('alone_login.html', form=login_form,
                                           msg="Неверный адрес электронной почты")  # Шаблон только с логином
                if not us.check_password(login_form.password.data):
                    return render_template('alone_login.html', form=login_form, msg="Неверный пароль")
                login_user(us, remember=login_form.remember_me.data)
                return redirect(f'/borrow_book/{code}')
            return render_template('alone_login.html', form=login_form)
        return render_template('message.html', msg='У этой книги нет владельца', form=form)
    else:
        return render_template('message.html', msg=f'Эта книга принадлежит {cur_book.owner}')


class LibraryView(FlaskView):
    @route('/')
    @login_required
    def index(self):
        session = db_session.create_session()
        books = []
        if current_user.role_id == session.query(Role).filter(Role.name == 'Librarian').first().id:
            for i in session.query(Book).all():
                if i.edition.library_id == current_user.library_id and i.owner:
                    books.append(i)
        else:
            for i in session.query(Book).all():
                if i.edition.library_id == current_user.library_id and i.owner_id == current_user.id:
                    books.append(i)
        return render_template('library.html')
        #  у ученика: Вы причислены к библиотек #{id библиотеки}
        #  Под надписью будет маленькая ссылка:
        #  Ошиблись библиотекой? <a href="ещё не придумал">Сменить номер библиотеки</a>
        #  (Здесь ссылка на случай, если библиотекарь по ошибке принял чужого ребенка)
        #  Под этой подписью список всех книг, которые он взял (с поиском)

        #  Если user - "Librarian", на сайте будет написано
        #  Вы управляете библиотекой #{id библиотеки}

        #  У каждого есть возможность изменить свой профиль
        #  А у библиотекаря так же имя школы

    @route('/editions')
    @login_required
    def editions(self):
        session = db_session.create_session()
        editions = session.query(Edition).filter(Edition.library_id == current_user.library_id).all()
        return render_template('editions.html')
        #  Эта вкладка доступна всем членам библиотеки
        #  Здесь будет находиться список всех изданий (editions)
        #  Под списком изданий понимается список ссылок на library/edition/{edition_id}
        #  У библиотекаря должна быть кнопка "Добавить книгу" (не "Добавить издание", слишком непонятно),
        #  добавляющее новое издание

    @route('/editions/<int:edition_id>')
    @login_required
    def edition(self, edition_id):
        session = db_session.create_session()
        edition = session.query(Edition).get(edition_id)
        if not edition:
            return abort(404, description='Книга не найдена')
        if edition.library_id != current_user.library_id:
            return abort(403, 'Эта книга приписана к другой библиотеке')
        books = session.query(Book).filter(Book.edition_id == edition_id).all()
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
        book = session.query(Book).get(book_id)
        if not book:
            return abort(404, description='Книга не найдена')
        if book.edition.library_id != current_user.library_id:
            return abort(403, 'Эта книга приписана к другой библиотеке')
        #  Здесь будут находиться
        #  id книги (именно книги, не издания)
        #  Информация об ИЗДАНИИ (тип название, автор, год издания и тд.)
        #  У библиотекаря есть такие же кнопки, как и рядом с каждой книгой в списке,
        #  А так же кнопка "Получить qr-код"

    @route('/students')
    @login_required
    def students(self):
        session = db_session.create_session()
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        if current_user.role_id != librarian_role.id:
            return abort(403, description='Сюда можно только библиотекарю')
        students = session.query(User).filter(User.role_id != librarian_role.id,
                                              User.library_id == current_user.library_id)
        # Здесь будет находиться список всех учащихся, привязанных к данной библиотеке
        # Список учащихся - спичок ссылок на library/students/{student_id}

    @route('/students/<int:user_id>')
    @login_required
    def student(self, user_id):
        session = db_session.create_session()
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        if current_user.role_id != librarian_role.id:
            return abort(403, description='Сюда можно только библиотекарю')
        student = session.query(User).get(user_id)
        if not student:
            return abort(404, description='Данный пользователь не найден')
        student_role = session.query(Role).filter(Role.name == 'Student').first()
        if student.role_id != student_role.id:
            return abort(403, description='Этот ученик из другой школы')

        #  Здесь библиотекарь видит Фамилию и Имя ученика
        #  И список всех книг, которые у него сейчас находятся
        #  P.S. это не профиль студента (я думаю, профили других людей будут недоступны)


LibraryView.register(app, route_base='/library')

if __name__ == '__main__':
    db_session.global_init('db/library.sqlite3')
    app.run(debug=True)
