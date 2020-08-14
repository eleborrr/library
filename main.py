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
from difflib import SequenceMatcher

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


@app.errorhandler(400)
def error_400(er):
    return render_template('плохой_запрос.html')


@app.errorhandler(401)
def error_401(er):
    return redirect('/sign_in#tab_03'), 401


@app.errorhandler(403)
def error_403(er):
    return render_template('тебе_сюда_нельзя.html'), 403


@app.errorhandler(404)
def error_404(er):
    return render_template('не_найдено.html'), 404


@app.errorhandler(500)
def error_500(er):
    return render_template('разрабы_тупые_криворученки.html'), 404


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


@app.route('/')
def index():
    return render_template('main.html')


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
        for i in session.query(Library).all():
            if i.check_id(register_form.library_id.data):
                lib_id = i.id
                break
        else:
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                                   login_form=login_form, tab_num=2, msg2="Неверный идентификатор библиотеки")
        register_student(register_form.name.data, register_form.surname.data, register_form.email.data, register_form.password.data, lib_id,
                         register_form.class_num.data)
        return redirect('/library')
    return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                           login_form=login_form, tab_num=3)


@app.route('/borrow_book/<string:code>')
def borrow_book(code):
    session = db_session.create_session()
    if not current_user.is_authenticated:
        form = LoginForm()
        if form.validate_on_submit():
            us = session.query(User).filter(User.login == form.email.data).first()
            if not us:
                return render_template('alone_login.html', form=form, msg="Неверный адрес электронной почты")  # Шаблон только с логином
            if not us.check_password(form.password.data):
                return render_template('alone_login.html', form=form, msg="Неверный пароль")
            login_user(us, remember=form.remember_me.data)
            return redirect(f'/borrow_book/{code}')
        return render_template('alone_login.html', form=form)
    for i in session.query(Book).all():
        if i.check_id(code):
            cur_book = i
            break
    else:
        return abort(404, messagge='Неверный идентификатор книги')  # Шаблон с сообщением в центре экрана
    if not cur_book.owner:
        cur_book.owner_id = current_user.id
        session.commit()
        form = BorrowBookForm()
        if form.validate_on_submit():
            cur_book.owner_id = current_user.id
            session.commit()
            session.close()
            return render_template('message.html', msg='Книга добавлена в ваш формуляр')
        return render_template('message.html', msg='У этой книги нет владельца', form=form)
    else:
        return render_template('message.html', msg=f'Эта книга принадлежит {cur_book.owner}')


class LibraryView(FlaskView):
    @route('/books')
    @login_required
    def books(self):
        session = db_session.create_session()
        filter_seed = request.args.get('filter')
        if filter_seed is None:
            filter_seed = ''
        query = session.query(Book).join(User).join(Edition).filter(Edition.library_id == current_user.libray_id)
        for i in filter_seed.split(','):
            attr, val = i.rsplit('_', 1)
            if attr == 'id':
                try:
                    val = int(val)
                except ValueError:
                    return abort(400)
                query = query.filter(Book.id == val)
            elif attr == 'edition_id':
                try:
                    val = int(val)
                except ValueError:
                    return abort(400)
                query = query.filter(Book.edition_id == val)
            elif attr == 'owner_id':
                try:
                    val = int(val)
                except ValueError:
                    return abort(400)
                query = query.filter(Book.owner_id == val)
            elif attr == 'name':
                query = query.filter(SequenceMatcher(None, Edition.name, val.lower().capitalize()).ratio() >= 0.6)
            elif attr == 'author':
                query = query.filter(SequenceMatcher(None, Edition.author, val.lower().capitalize()).ratio() >= 0.6)
            elif attr == 'publication_year':
                try:
                    val = int(val)
                except ValueError:
                    return abort(400)
                query = query.filter(Edition.publication_year == val)
            elif attr == 'owner_surname':
                query = query.filter(SequenceMatcher(None, User.surname, val.lower().capitalize()).ratio() >= 0.6)
            else:
                return abort(400)

        result = query.all()
        return render_template('smt.html', result=result, mode='book')  # mode говорит о том, какой тип элементов в result

    @route('/editions')
    def editions(self):
        session = db_session.create_session()
        filter_seed = request.args.get('filter')
        if filter_seed is None:
            filter_seed = ''
        query = session.query(Edition).filter(Edition.library_id == current_user.library_id)
        kwargs = {
            'id': '',
            'name': '',
            'author': '',
            'publication_year': '',
            'edition_id': '',
            'owner_id': '',
            'owner_surname': ''
        }
        for i in filter_seed.split(','):
            attr, val = i.rsplit('_', 1)
            if attr == 'id':
                try:
                    val = int(val)
                except ValueError:
                    return abort(400)
                query = query.filter(Edition.id == val)
            elif attr == 'name':
                query = query.filter(SequenceMatcher(None, Edition.name, val.lower().capitalize()).ratio() >= 0.6)
            elif attr == 'author':
                query = query.filter(SequenceMatcher(None, Edition.author, val.lower().capitalize()).ratio() >= 0.6)
            elif attr == 'publication_year':
                try:
                    val = int(val)
                except ValueError:
                    return abort(400)
                query = query.filter(Edition.publication_year == val)
            else:
                return abort(400)
            kwargs[attr] = val
        form = book_filter_form(**kwargs)
        if form.validate_on_submit():
            final = '/library/books'
            args = []
            for i in kwargs:
                res = getattr(form, i).data
                if res:
                    args.append(f'{i}_{res}')
            if args:
                final += '?filter='
                final += ','.join(args)
            return redirect(final)
        result = query.all()
        return render_template('smt.html', result=result, mode='edition', form=form)

    @route('/students')
    def students(self):
        session = db_session.create_session()
        filter_seed = request.args.get('filter')
        if filter_seed is None:
            filter_seed = ''
        query = session.query(User).join(Role).filter(User.library_id == current_user.library_id, Role.name == 'Student')
        for i in filter_seed.split(','):
            attr, val = i.rsplit('_', 1)
            if attr == 'id':
                try:
                    val = int(val)
                except ValueError:
                    return abort(400)
                query = query.filter(User.id == val)
            elif attr == 'name':
                query = query.filter(SequenceMatcher(None, User.name, val.lower().capitalize()).ratio() >= 0.6)
            elif attr == 'surname':
                query = query.filter(SequenceMatcher(None, User.surname, val.lower().capitalize()).ratio() >= 0.6)
            elif attr == 'class_num':
                try:
                    val = int(val)
                except ValueError:
                    return abort(400)
                query = query.filter(User.class_num == val)
            else:
                return abort(400)

            result = query.all()
            return render_template('smt.html', result=result, mode='user')

    @route('/edition/<int:edition_id>')
    def edition(self, edition_id):
        pass  # Здесь будет инфо об издании и список qr-кодов всех его книг

    @route('/book/<int:book_id>')
    def book(self, book_id):
        pass  # Здесь будет инфо о книге и его qr-код


if __name__ == '__main__':
    db_session.global_init('db/library.sqlite3')
    app.run(debug=True)

