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
from sequence_matcher import SequenceMatcher
from data import db_session
import logging
from logging.handlers import RotatingFileHandler




def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
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
    res = _create_qr_list([(x.generate_id(), x.id) for x in session.query(Edition).get(edition_id).books])[0]
    session.close()
    return res


def delete_edition(edition_id):
    session = db_session.create_session()
    ed = session.query(Edition).get(edition_id)
    book_owner = False
    if ed:
        for book in ed.books:
            if book.owner:
                book_owner = True
                break
            session.delete(book)
            session.commit()
        if not book_owner:
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
    return redirect('/sign_in#tab_03'), 401


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

@application.errorhandler(404)
def error_404(er):
    if er.description == 'The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.':
        er.description = 'Страница не найдена'
    return render_template('404.html', msg=er.description), 404

#
# @app.errorhandler(500)
# def error_500(er):
#     return render_template('.html', msg=er.message)



@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    try:
        return session.query(User).get(user_id)
    finally:
        session.close()


@application.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@application.before_first_request
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


@application.route("/zhoppa")
def hello():
   return "<h1 style='color:blue'>Hello There!</h1>"

   
@application.route("/")
def zhoppa():
    return render_template("index.html")

    
@application.route('/sign_in', methods=['GET', 'POST'])
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
            return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
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
        login_user(ex)
        return redirect('/library')
    return render_template('tabs-page.html', library_form=library_form, register_form=register_form,
                           login_form=login_form, tab_num=3)


def confirm_email_decorator(func):
    def new_func(*args, **kwargs):
        try:
            if current_user.confirmed:
                return func(*args, **kwargs)
            else:
                return redirect('/confirm_email')
        except AttributeError:
            return func(*args, **kwargs)

    return new_func


@app.route('/borrow_book/<string:code>', methods=["GET", "POST"])

def borrow_book(code):
    session = db_session.create_session()
    for i in session.query(Book).all():
        if i.check_id(code):
            cur_book = i
            break
    else:
        return abort(404, description='Неверный идентификатор книги')  # Шаблон с сообщением в центре экрана

    form = BorrowBookForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        if current_user.library_id == cur_book.edition.library_id:
            lend_book(current_user.id, cur_book.id)
            return redirect('/library/')
        else:
            return render_template('message.html',
                                   msg='Эта книга принадлежит другой библиотеке!')  # отнеси ее туда, не будь говнюком
    return render_template('borrow_book.html', msg='У этой книги нет владельца', form=form, book=cur_book, owner=cur_book.owner, cur_user=current_user)
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
    @route('/books')
    @route('/')
    @login_required
    def index(self):
        session = db_session.create_session()
        id_, name, author = request.args.get('id'), request.args.get('name'), request.args.get('author')
        publication_year, edition_id, owner_id, owner_surname, free = request.args.get('publication_year'), request.args.get(
            'edition_id'), request.args.get('owner_id'), request.args.get('owner_surname'), request.args.get('free')

        query = session.query(Book).join(Edition).filter(Edition.library_id == current_user.library_id)
        kwargs = {
            'id': '',
            'name': '',
            'author': '',
            'publication_year': '',
            'edition_id': '',
            'owner_id': '',
            'owner_surname': '',
            'free': ''
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
        if free:
            query = query.filter(Book.owner_id == None)
            kwargs['free'] = free
        result = query.all()
        new_res = []
        for i in result:
            flag = True
            if name:
                kwargs['name'] = name
                if not match(i.edition.name.lower(), name.lower()):
                    flag = False
            if author:
                kwargs['author'] = author
                if not match(i.edition.author.lower(), author.lower()):
                    flag = False
            if owner_surname:
                kwargs['owner_surname'] = owner_surname
                try:
                    if not match(i.owner.surname.lower(), owner_surname.lower()):
                        flag = False
                except AttributeError:
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
                               form=form, library_code=library.generate_id(), current_user=cur_user)
        #  у ученика: Вы причислены к библиотек #{id библиотеки}
        #  Под надписью будет маленькая ссылка:
        #  Ошиблись библиотекой? <a href="ещё не придумал">Сменить номер библиотеки</a>
        #  (Здесь ссылка на случай, если библиотекарь по ошибке принял чужого ребенка)
        #  Под этой подписью список всех книг, которые он взял (с поиском)

        #  Если user - "Librarian", на сайте будет написано
        #  Вы управляете библиотекой #{id библиотеки}

        #  У каждого есть возможность изменить свой профиль
        #  А у библиотекаря так же имя школы

    @route('/editions', methods=['GET', 'POST'], strict_slashes=False)
    @login_required
    def editions(self):
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
        form = edition_filter_form(**kwargs)
        result = query.all()
        new_res = []
        for i in result:
            flag = True
            if name:
                kwargs['name'] = name
                if not match(i.name.lower(), name.lower()):
                    flag = False
            if author:
                kwargs['author'] = author
                if not match(i.author.lower(), author.lower()):
                    flag = False
            if flag:
                new_res.append(i)
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
                               current_user=current_user, url_for=url_for)

    @route('/editions/<int:edition_id>', methods=['GET', 'POST'])
    @login_required
    def edition(self, edition_id):
        session = db_session.create_session()
        edition = session.query(Edition).get(edition_id)
        if not edition:
            return abort(404, description='Книга не найдена')
        if edition.library_id != current_user.library_id:
            return abort(403, 'Эта книга приписана к другой библиотеке')
        books = session.query(Book).filter(Book.edition_id == edition_id).all()
        res = generate_edition_qr(edition_id)
        return render_template('editionone.html', books=books, count_books=len(books), edition=edition, url_for=url_for,
                               current_user=current_user, lists=res)

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

    @route('/books/<int:book_id>', methods=['GET'])
    @login_required
    def book(self, book_id):
        session = db_session.create_session()
        book = session.query(Book).get(book_id)
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

    @route('/students', methods=['GET', 'POST'], strict_slashes=False)
    @login_required
    def students(self):
        session = db_session.create_session()
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        if current_user.role_id != librarian_role.id:
            return abort(403, description='Сюда можно только библиотекарю')
        id_, surname, class_num = request.args.get('id'), request.args.get('surname'), request.args.get('class_num')
        kwargs = {
            'id': '',
            'name': '',
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

        result = query.all()
        new_res = []
        for i in result:
            if surname:
                kwargs['surname'] = surname
                if match(i.surname.lower(), surname.lower()):
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
        library_code = session.query(Library).get(current_user.library_id).generate_id()
        return render_template('students.html', students=new_res, form=form, library_code=library_code)
        # Здесь будет находиться список всех учащихся, привязанных к данной библиотеке
        # Список учащихся - спичок ссылок на library/students/{student_id}

    @route('/profile', methods=['GET', 'POST'])
    @login_required
    def student(self, user_id):
        session = db_session.create_session()
        user = session.query(User).get(current_user.id)
        library = session.query(Library).get(current_user.library_id)
        if user.role_id == 2:
            library_form = edit_library(
                **{'name': user.name, 'surname': user.surname, 'students_join_possibility': library.opened,
                   'library_school_name': library.school_name})
            if library_form.validate_on_submit():
                if library_form.library_school_name.data:
                    library.school_name = library_form.library_school_name.data
                if library_form.students_join_possibility.data:
                    # library.opened = library_form.students_join_possibility.data
                    library.opened = True
                else:
                    library.opened = False
                if library_form.name.data:
                    user.name = library_form.name.data
                if library_form.surname.data:
                    user.surname = library_form.surname.data
                session.commit()
            library_code = session.query(Library).get(current_user.library_id).generate_id()
            return render_template('library_edit.html', form=library_form, current_user=current_user, library_code=library_code)
        else:
            student_form = edit_student_profile_form(name=current_user.name, surname=current_user.surname)
            if student_form.validate_on_submit():
                if student_form.name.data:
                    user.name = student_form.name.data
                if student_form.surname.data:
                    user.surname = student_form.surname.data
                session.commit()
            # if True: # через кнопку
            #     if user.books:
            #         print('Нельзя, ты книги не сдал, бро')
            #     else:  #popup с кодом новой библиотеки или кнопка "отвязаться от библиотеки"
            #         user.library_id = 'NULL'
            #         user.role_id = 3
            library_code = ''
            if user.role_id == 1:
                library_code = session.query(Library).get(current_user.library_id).generate_id()
            return render_template('library_edit.html', form=student_form, current_user=current_user, library_code=library_code)

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
        return render_template('profile-st.html', books=books, user=current_user)

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
        return render_template('give_book.html', form=form, book=book)

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
                if i.string_id == id_:
                    if i.opened:
                        us = session.query(User).get(current_user.id)
                        us.library_id = i.id
                        us.role_id = 1
                        session.commit()
                        session.close()
                        break
                    else:
                        return render_template('join.html', form=form,
                                               message='Доступ к этой библиотеке закрыт, обратитесь к библиотекарю')
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

    @login_required
    @route('/delete_student/<int:student_id>')
    def delete_student(self, student_id):
        if current_user.role_id != 2:
            return abort(403, description='Эта функция достурна лишь библиотекарю')
        session = db_session.create_session()
        student = session.query(User).get(student_id)
        if not student:
            return abort(404, description='Пользователь не найден')
        if student.role_id != 1 or student.library_id != current_user.library_id:
            return abort(403, description='Такого ученика нет в вашей библиотеке')
        student.role_id = 3
        student.library_id = None
        session.commit()
        return redirect('/library/students')


LibraryView.register(app, '/library')

if __name__ == "__main__":
   application.run(host='0.0.0.0')
