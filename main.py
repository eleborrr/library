from flask import Flask, redirect, render_template, abort, request, url_for, render_template_string, Markup
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
from sequence_matcher import match
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import uuid
import os

app = Flask(__name__)
login_manager = LoginManager(app)
app.config.from_object(AppConfig)
mail = Mail(app)

if __name__ != 'tests.py':
    db_session.global_init('db/library.sqlite3')


def generate_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        print(email)
    except Exception:
        return False
    return email


def send_email(user, target):
    email = user.login
    token = generate_token(email)
    if target == 1:  # confirm email
        link = f'confirm_email/{token}'
        template = render_template_string('Для подтверждения адреса электронной почты'
                                          'перейдите по ссылке {{ link }}', link=link)  # Можно вынести в отдельный файл
        subject = 'Подтверждение адреса электронной почте на сайте libby.ru'
    elif target == 2:  # change password:
        link = f'change_password/{token}'
        template = render_template_string('Для смены пароля перейдите '
                                          'по ссылке {{ link }}', link=link)  # Можно вынести в отдельный файл
        subject = 'Изменение пароля к аккаунту на сайте libby.ru'
    else:
        raise ValueError
    message = Message(subject=subject, recipients=[email], html=template)
    mail.send(message)


def create_library(school_name, **librarian_data):  # login, name, surname, password
    session = db_session.create_session()
    lib = Library(school_name=school_name)
    session.add(lib)
    session.commit()
    role_id = session.query(Role).filter(Role.name == 'Librarian').first().id
    user = User(**librarian_data, role_id=role_id, library_id=lib.id,
                class_num=None)
    session.add(user)
    try:
        login_user(user)
    except Exception:
        pass
    session.commit()
    session.close()


def add_edition(library_id, count, **edition_data):  # name, author, publication_year, ed_name
    session = db_session.create_session()
    edition = Edition(**edition_data, library_id=library_id)
    session.add(edition)
    session.commit()
    for i in range(count):
        session.add(Book(edition_id=edition.id))
    session.commit()
    session.close()


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
    role_id = session.query(Role).filter(Role.name == 'StudentWithoutLibrary').first().id
    if not ex_user:
        us = User(name=name, surname=surname, password=password, role_id=role_id, library_id=library_id,
                  class_num=class_num, login=login)
        session.add(us)
        try:
            login_user(us)
        except Exception:
            pass
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
    session.close()


def delete_edition(edition_id):
    session = db_session.create_session()
    ed = session.query(Edition).get(edition_id)
    if ed:
        session.delete(ed)
        session.commit()
        session.close()
        return 0
    return 1


def delete_book(book_id):
    session = db_session.create_session()
    book = session.query(Book).get(book_id)
    if book:
        session.delete(book)
        session.commit()
        session.close()
        return 0
    return 1


def get_user_by_token(token, session):
    email = confirm_token(token)
    user = session.query(User).filter(User.login == email).first()
    return user


@app.errorhandler(401)
def error_401(er):
    return redirect('/sign_in#tab_03')


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
    return render_template('404.html', msg=er.description, url_for=url_for)


#
# @app.errorhandler(500)
# def error_500(er):
#     return render_template('разрабы_тупые_криворученки.html', msg=er.message)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    try:
        return session.query(User).get(user_id)
    finally:
        session.close()


@app.route('/test_send_emails')
@login_required
def send_emails():
    send_email(current_user, 1)
    send_email(current_user, 2)
    return 'Отправлено'


@app.route('/confirm_email/<string:token>')
def confirm_email(token):
    session = db_session.create_session()
    user = get_user_by_token(token, session)
    if not user:
        return 'Токен не действителен'
    user.confirmed = True
    session.commit()
    session.close()
    return 'Адрес электронной почты был подтвержден'


@app.route('/change_password/<string:token>', methods=['GET', 'POST'])
def change_password(token):
    session = db_session.create_session()
    user = get_user_by_token(token, session)
    if not user:
        return 'Токен не действителен'
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        session.commit()
        return 'Пароль был изменён'
    return render_template('change_password.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.before_first_request
def create_roles():
    session = db_session.create_session()
    roles = ['Student', 'Librarian', 'StudentWithoutLibrary']
    for i in session.query(Role).all():
        roles.remove(i.name)
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
        register_student(register_form.name.data, register_form.surname.data, register_form.email.data,
                         register_form.password.data, None,
                         register_form.class_num.data)
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


def check_int_type(el):
    try:
        el = int(el)
    except ValueError:
        return abort(400)
    return el


class LibraryView(FlaskView):
    @route('/books', methods=['GET', 'POST'])
    @route('/', methods=['GET', 'POST'])
    @login_required
    def index(self):
        def markup(book_id_):
            string = f"""<div class='popup' id='popup_book_{book_id_}'>
            <a class="popup__area" href='#header'></a>
            <div class='popup__body'>
                <div class='popup__content'>
                    <a class='popup__close' href='#header'>X</a>
                    <div><h3> Точно удалить? </h3></div>
                    <form class='form_up' method="post">

                        <a class="link-delete opas" href="/library/delete_book/{book_id_}"
                           style="border: none;cursor: pointer;color: white">Удалить</a>
                        <a class="link-delete opas" href="/library/books"
                           style="border: none;cursor: pointer;color: white;background-color: #C1F084">Вернуться</a>
                    </form>
                </div>
            </div>

        </div>"""
            return Markup(string)
        if current_user.role_id == 3:
            return redirect('/library/join')
        session = db_session.create_session()
        id_, name, author = request.args.get('id'), request.args.get('name'), request.args.get('author')
        publication_year, edition_id, owner_id, owner_surname = request.args.get('publication_year'), request.args.get(
            'edition_id'), request.args.get('owner_id'), request.args.get('owner_surname')

        query = session.query(Book).join(Edition).filter(Edition.library_id == current_user.library_id)
        kwargs = {
            'id': '',
            'name': '',
            'author': '',
            'publication_year': '',
            'edition_id': '',
            'owner_id': '',
            'owner_surname': ''
        }

        if id_:
            query = query.filter(Book.id == check_int_type(id_))
            kwargs['id'] = id_
        if publication_year:
            query = query.filter(Edition.publication_year == check_int_type(publication_year))
            kwargs['publication_year'] = publication_year
        if edition_id:
            query = query.filter(Book.edition_id == check_int_type(edition_id))
            kwargs['edition_id'] = edition_id
        if owner_id:
            query = query.filter(Book.owner_id == check_int_type(owner_id))
            kwargs['owner_id'] = owner_id
        result = query.all()
        new_res = []
        for i in result:
            flag = True
            if name:
                kwargs['name'] = name
                if not match(i.edition.name, name):
                    flag = False
            if author:
                kwargs['author'] = author
                if not match(i.edition.author, author):
                    flag = False
            if owner_surname:
                kwargs['owner_surname'] = owner_surname
                if not match(i.owner.surname, owner_surname):
                    flag = False
            if flag:
                new_res.append(i)
        form = book_filter_form(**kwargs)
        if form.validate_on_submit():
            final = '/library/books'
            args = []
            for i in kwargs:
                res = getattr(form, i).data
                if res:
                    args.append(f'{i}={res}')
            if args:
                final += '?'
                final += '&'.join(args)
            return redirect(final)
        library = session.query(Library).get(current_user.library_id)
        cur_user = session.query(User).get(current_user.id)
        return render_template('library.html', books=new_res, mode='book',
                               form=form, library_code=library.generate_id(), current_user=cur_user, markup=markup)
        #  у ученика: Вы причислены к библиотек #{id библиотеки}
        #  Под надписью будет маленькая ссылка:
        #  Ошиблись библиотекой? <a href="ещё не придумал">Сменить номер библиотеки</a>
        #  (Здесь ссылка на случай, если библиотекарь по ошибке принял чужого ребенка)
        #  Под этой подписью список всех книг, которые он взял (с поиском)

        #  Если user - "Librarian", на сайте будет написано
        #  Вы управляете библиотекой #{id библиотеки}

        #  У каждого есть возможность изменить свой профиль
        #  А у библиотекаря так же имя школы

    @route('/editions', methods=['GET', 'POST'])
    @login_required
    def editions(self):
        if current_user.role_id == 3:
            return redirect('/library/join')
        def markup(edition_id):
            string = f"""<div class='popup' id='popup_edition_{edition_id}'>
    <a class="popup__area" href='#header'></a>
    <div class='popup__body'>
        <div class='popup__content'>
            <a class='popup__close' href='#header'>X</a>
            <div><h3> Точно удалить? </h3></div>
            <form class='form_up' method="post">

                <a class="link-delete opas" href="/library/delete_edition/{ edition_id }"
                   style="border: none;cursor: pointer;color: white">Удалить</a>
                <a class="link-delete opas" href="/library/editions"
                   style="border: none;cursor: pointer;color: white;background-color: #C1F084">Вернуться</a>
            </form>
        </div>
    </div>

</div>"""
            return Markup(string)

        session = db_session.create_session()
        id_, name, author = request.args.get('id'), request.args.get('name'), request.args.get('author')
        publication_year, edition_id, owner_id, owner_surname = request.args.get('publication_year'), request.args.get(
            'edition_id'), request.args.get('owner_id'), request.args.get('owner_surname')
        kwargs = {
            'id': '',
            'name': '',
            'author': '',
            'publication_year': ''
        }
        query = session.query(Edition).filter(Edition.library_id == current_user.library_id)
        if id_:
            query = query.filter(Edition.id == check_int_type(id_))
            kwargs['id'] = id_
        if publication_year:
            query = query.filter(Edition.publication_year == check_int_type(publication_year))
            kwargs['publication_year'] = publication_year
        result = query.all()
        new_res = []
        for i in result:
            flag = True
            if name:
                kwargs['name'] = name
                if not match(i.name, name):
                    flag = False
            if author:
                kwargs['author'] = author
                if not match(i.author, author):
                    flag = False
            if flag:
                new_res.append(i)
        form = edition_filter_form(**kwargs)
        if form.validate_on_submit():
            final = '/library/editions'
            args = []
            for i in kwargs:
                res = getattr(form, i).data
                if res:
                    args.append(f'{i}={res}')
            if args:
                final += '?'
                final += '&'.join(args)
            return redirect(final)
        library_code = session.query(Library).get(current_user.library_id).generate_id()
        return render_template('editions.html', editions=new_res, form=form, library_code=library_code, markup=markup,
                               current_user=current_user)
        #  Эта вкладка доступна всем членам библиотеки
        #  Здесь будет находиться список всех изданий (editions)
        #  Под списком изданий понимается список ссылок на library/edition/{edition_id}
        #  У библиотекаря должна быть кнопка "Добавить книгу" (не "Добавить издание", слишком непонятно),
        #  добавляющее новое издание

    @route('/editions/<int:edition_id>', methods=['GET', 'POST'])
    @login_required
    def edition(self, edition_id):
        if current_user.role_id == 3:
            return redirect('/library/join')
        session = db_session.create_session()
        edition = session.query(Edition).get(edition_id)
        if not edition:
            return abort(404, description='Книга не найдена')
        if edition.library_id != current_user.library_id:
            return abort(403, 'Эта книга приписана к другой библиотеке')
        books = session.query(Book).filter(Book.edition_id == edition_id).all()
        return render_template('editionone.html', books=books, count_books=len(books), edition=edition, url_for=url_for,
                               current_user=current_user)
        # Сдесь будет список книг данного издания с их текущими владельцами
        # У библиотекаря рядом с каждой книгой есть кнопка "Вернуть в библиотеку" или "Одолжить книгу"
        # (Я думаю у библиотекаря должна быть возможность одалживать книгу вручную),
        # А так эе кнопка "Удалить" (Вдруг случайно лишнюю создала") P.s кнопка недоступна, если книга не в библиотеке
        # Так же библиотекарю доступна кнопка "Добавить книгу", добавляющая новую книгу этого издания,
        # и кнопка "список qr-кодов"

    @route('/editions/create', methods=['GET', 'POST'])
    @login_required
    def create_edition(self):
        if current_user.role_id != 2:
            return redirect('/library')
        session = db_session.create_session()
        form = CreateEdition()
        if form.validate_on_submit():
            edition = Edition()
            edition.name = form.name.data
            edition.library_id = current_user.library_id
            edition.ed_name = form.publisher_name.data
            edition.author = form.author.data
            edition.publication_year = form.publication_year.data
            filename = str(uuid.uuid4()) + '.jpg'
            try:
                os.makedirs('/static/img/editions')
            except FileExistsError:
                pass
            filedata_ = form.photo.data
            filedata_.save('static/img/editions/' + filename)
            edition.photo_name = filename
            session.add(edition)
            session.commit()
            for i in range(int(form.book_counts.data)):
                book = Book()
                book.edition_id = edition.id
                session.add(book)
                session.commit()
            return redirect(f'/library/editions/{edition.id}')
        return render_template('create_edition_form.html', form=form, url_for=url_for)

    @route('/books/<int:book_id>', methods=['GET', 'POST'])
    @login_required
    def book(self, book_id):
        if current_user.role_id == 3:
            return redirect('/library/join')
        session = db_session.create_session()
        book = session.query(Book).get(book_id)
        # print(book.owner)
        if not book:
            return abort(404, description='Книга не найдена')
        if book.edition.library_id != current_user.library_id:
            return abort(403, 'Эта книга приписана к другой библиотеке')
        if request.method == 'POST':
            try:
                if request.form['return-book']:
                    return_book(book_id)
            except Exception:
                pass
            try:
                if request.form['give-book']:
                    pass
            except Exception:
                pass
            try:
                if request.form['delete-book']:
                    remove_book(book_id)
            except Exception:
                pass
            try:
                if request.form['add-in-edition']:
                    pass
            except Exception:
                pass
            try:
                if request.form['print-qr']:
                    pass
            except Exception:
                pass
            try:
                if request.form['take-book']:
                    lend_book(current_user.id, book_id)
            except Exception:
                pass
            return redirect('/library/books/' + str(book_id))
        return render_template('bookone.html', book=book, user=current_user)
        #  Здесь будут находиться
        #  id книги (именно книги, не издания)
        #  Информация об ИЗДАНИИ (тип название, автор, год издания и тд.)
        #  У библиотекаря есть такие же кнопки, как и рядом с каждой книгой в списке,
        #  А так же кнопка "Получить qr-код"

    @route('/students', methods=['GET', 'POST'])
    @login_required
    def students(self):
        if current_user.role_id == 3:
            return redirect('/library/join')
        session = db_session.create_session()
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        if current_user.role_id != librarian_role.id:
            return abort(403, description='Сюда можно только библиотекарю')
        id_, surname, class_num, class_letter = request.args.get('id'), request.args.get('surname'), request.args.get(
            'class_num'), \
                                                request.args.get('class_letter')
        kwargs = {
            'id': '',
            'surname': '',
            'class_num': '',
            'class_letter': ''
        }
        query = session.query(User).join(Role).filter(User.library_id == current_user.library_id,
                                                      Role.name == 'Student')
        if id_:
            query = query.filter(User.id == check_int_type(id_))
            kwargs['id'] = id_
        if class_num:
            query = query.filter(User.class_num == check_int_type(class_num))
            kwargs['author'] = class_num
        if class_letter:
            query = query.filter(User.class_letter in [class_letter.lower(), class_letter.upper()])
            kwargs['class_letter'] = class_letter

        result = query.all()
        new_res = []
        for i in result:
            if surname:
                kwargs['surname'] = surname
                if match(i.surname, surname):
                    new_res.append(i)
            else:
                new_res.append(i)
        form = student_filter_form(**kwargs)
        if form.validate_on_submit():
            final = '/library/students'
            args = []
            for i in kwargs:
                res = getattr(form, i).data
                if res:
                    args.append(f'{i}={res}')
            if args:
                final += '?'
                final += '&'.join(args)
            return redirect(final)
        return render_template('students.html', students=new_res, form=form)
        # Здесь будет находиться список всех учащихся, привязанных к данной библиотеке
        # Список учащихся - спичок ссылок на library/students/{student_id}

    @route('/students/<int:user_id>', methods=['GET', 'POST'])
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
        return render_template('profile.html', user=student, current_user=current_user)
        #  Здесь библиотекарь видит Фамилию и Имя ученика
        #  И список всех книг, которые у него сейчас находятся
        #  P.S. это не профиль студента (я думаю, профили других людей будут недоступны)


    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile_main(self):
        session = db_session.create_session()
        user = session.query(User).get(current_user.id)
        library = session.query(Library).get(current_user.library_id)
        form = EditLibrary()
        if user.role != 'Teacher':
            #ошибку
            pass
        else:
            if form.validate_on_submit():
                if form.library_school_name.data:
                    library.school_name = form.library_school_name.data
                if form.students_join_possibility.data:
                    # добавить в бд к библиотеке это поле
                    pass
                if form.name.data:
                    user.name = form.name.data
                if form.surname.data:
                    user.surname = form.surname.data
                session.commit()
            return render_template('library_edit.html')


    @route('/profile/<int:student_id>', methods=['GET', 'POST'])
    @login_required
    def profile(self, student_id):
        session = db_session.create_session()
        student_role = session.query(Role).filter(Role.name == 'Student').first()
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        student = session.query(User).get(student_id)
        if not student:
            return abort(404, description='Такого ученика нет')
        if student.role_id == librarian_role.id:
            return redirect('/library')
        if current_user.role_id == student_role.id:
            return abort(403, description='Сюда можно только библиотекарю')
        if current_user.library_id != session.query(User).get(student_id).library_id:
            return abort(403, description='Пользователь не в вашей библиотеке')
        books = session.query(Book).filter(Book.owner_id == student_id).all()
        return render_template('profile.html', books=books, user=current_user)

    @login_required
    @route('/delete_edition/<int:id>')
    def delete_edition(self, id):
        session = db_session.create_session()
        if current_user.role_id != 2:
            return abort(403, description="Эта функция доступна только библиотекарю")
        ed = session.query(Edition).get(id)
        if not ed:
            return abort(404, description="Неизвестная книга")
        if ed.library_id != current_user.library_id:
            abort(403, description="Это издание относится к другой библиотеке")
        delete_edition(id)
        return redirect('/library/editions')

    @login_required
    @route('/delete_book/<int:id>')
    def delete_book(self, id):
        session = db_session.create_session()
        if current_user.role_id != 2:
            return abort(403, description="Эта функция доступна только библиотекарю")
        book = session.query(Book).get(id)
        if not book:
            return abort(404, description="Неизвестная книга")
        if book.edition.library_id != current_user.library_id:
            abort(403, description="Это издание относится к другой библиотеке")
        delete_book(id)
        return redirect('/library/books')

    @login_required
    @route('/add_book/<int:edition_id>')
    def add_book(self, edition_id):
        if current_user.role_id == 2:
            session = db_session.create_session()
            ed = session.query(Edition).get(edition_id)
            if ed:
                if ed.library_id == current_user.library_id:
                    session.close()
                    add_book(edition_id)
                else:
                    abort(403, description="Эта книга относится к другой библиотеке")
            else:
                abort(404, description="Издание не найдено")
        return redirect(f'/library/editions/{edition_id}')

    @login_required
    @route('/give_book/<int:book_id>', methods=['GET', 'POST'])
    def give_book(self, book_id):
        session = db_session.create_session()
        book = session.query(Book).get(book_id)
        if not book:
            return abort(404, description="Неизвестная книга")
        if current_user.role_id != 2:
            return abort(403, description="Данная функция доступна только библиотекарю")
        if book.edition.library_id != current_user.library_id:
            return abort(403, description="Эта книга не из вашей библиотеки")
        students = session.query(User).filter(User.role_id == 1, User.library_id == current_user.library_id).all()
        form = give_book_form(students)
        if form.validate_on_submit():
            st_id = form.select_student.data
            book.owner_id = st_id
            session.commit()
            session.close()
            return redirect('/library')
        return render_template('give_book.html', form=form)

    @login_required
    @route('/join', methods=['GET', 'POST'])
    def join(self):
        if current_user.role_id != 3:
            return redirect('/library')
        form = JoinLibraryForm()
        if form.validate_on_submit():
            id_ = form.id.data
            session = db_session.create_session()
            library = session.query(Library).all()
            for i in library:
                print(i.string_id)
                if i.string_id == id_:
                    us = session.query(User).get(current_user.id)
                    us.library_id = i.id
                    us.role_id = 1
                    print(current_user.role_id)
                    print(current_user.login)
                    session.commit()
                    session.close()
                    break
            else:
                return render_template('join.html', form=form, message='Неизвестный идентификатор')
            return redirect('/library')
        return render_template('join.html', form=form)

    @login_required
    @route('/return_book/<int:book_id>')
    def return_book(self, book_id):
        session = db_session.create_session()
        if current_user.role_id != 2:
            return abort(403, description="Данная функция доступна лишь библиотекарю")
        book = session.query(Book).get(book_id)
        if not book:
            return abort(404, description="Такой книги нет в библиотеке")
        if current_user.library_id != book.edition.library_id:
            return abort(403, description="Эта книга находится не в вашей библиотеке")
        book.owner_id = None
        session.commit()
        session.close()
        return redirect('/library')



LibraryView.register(app)

if __name__ == '__main__':
    # db_session.global_init('db/library.sqlite3')
    app.run(debug=True)
