from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, BooleanField, TextAreaField, DateTimeField, \
    DateField, TimeField, FileField, IntegerField, SelectField
from wtforms.fields.html5 import EmailField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, NumberRange, EqualTo
from flask_wtf.recaptcha import RecaptchaField
from datetime import datetime


class OptionalIntegerField(IntegerField):
    def process_data(self, value):
        if not value:
            value = None
        IntegerField.process_data(self, value)

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = int(valuelist[0])
            except ValueError:
                self.data = None
                if valuelist[0]:
                    raise ValueError(self.gettext('Not a valid integer value'))


class CreateLibraryForm(FlaskForm):  # Создает пользователя-библиотекаря и библиотеку
    name = StringField('Имя', validators=[DataRequired(), Length(max=32)])
    surname = StringField('Фамилия', validators=[DataRequired(), Length(max=32)])
    email = EmailField('Адрес электронной почты', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(max=128)])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired(), Length(max=128)])
    library_school_name = StringField('Наименование школы (полное)', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Зарегистрироваться')


class RegisterStudentForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(max=32)])
    surname = StringField('Фамилия', validators=[DataRequired(), Length(max=32)])
    email = EmailField('Адрес электронной почты', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(max=128)])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired(), Length(max=128)])
    class_num = IntegerField('Номер класса, в котором вы учитесь', validators=[DataRequired(),
                                                                               NumberRange(min=1, max=11)])
    submit = SubmitField('Зарегистрироваться')


def edit_library(**kwargs):
    class EditLibrary(FlaskForm):
        name = StringField('Имя', validators=[DataRequired(), Length(max=32)], default=kwargs.get('name'))
        surname = StringField('Фамилия', validators=[DataRequired(), Length(max=32)], default=kwargs.get('surname'))
        students_join_possibility = BooleanField('Разрешить регистрацию', default=kwargs.get('students_join_possibility'))
        library_school_name = StringField('Наименование школы (полное)', validators=[DataRequired(), Length(max=64)],
                                          default=kwargs.get('library_school_name'))
        submit = SubmitField('Сохранить')
    return EditLibrary()


class CreateEdition(FlaskForm):
    name = StringField("Название книги")
    publisher_name = StringField("Издательство")
    author = StringField("Фамилия автора")
    publication_year = IntegerField("Год публикации")
    book_counts = IntegerField("Количество книг")
    submit = SubmitField("Создать")
    photo = FileField("Обложка")


class LoginForm(FlaskForm):
    email = EmailField('Адрес электронной почты')
    password = PasswordField('Пароль')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class BorrowBookForm(FlaskForm):
    submit = SubmitField('Взять книгу')


def book_filter_form(**kwargs):
    class BookFilterForm(FlaskForm):
        id = OptionalIntegerField('Номер книги', default=kwargs['id'])
        name = StringField('Название книги', default=kwargs['name'])
        author = StringField('Фамилия автора', default=kwargs['author'])
        publication_year = OptionalIntegerField('Год публикации', default=kwargs['publication_year'])
        edition_id = OptionalIntegerField('Номер издания', default=kwargs['edition_id'])
        owner_id = OptionalIntegerField('Номер владельца', default=kwargs['owner_id'])
        owner_surname = StringField('Фамилия владельца', default=kwargs['owner_surname'])
        submit = SubmitField('Искать')

    return BookFilterForm()


def edition_filter_form(**kwargs):
    class EditionFilterForm(FlaskForm):
        id = OptionalIntegerField('Номер издания', default=kwargs['id'])
        name = StringField('Название книги', default=kwargs['name'])
        author = StringField('Фамилия автора', default=kwargs['author'])
        publication_year = OptionalIntegerField('Год публикации', default=kwargs['publication_year'])
        submit = SubmitField('Искать')

    return EditionFilterForm()


def student_filter_form(**kwargs):
    class StudentFilterForm(FlaskForm):
        id = OptionalIntegerField('Номер ученика', default=kwargs['id'])
        surname = StringField('Фамилия ученика', default=kwargs['surname'])
        class_num = OptionalIntegerField('Номер класса ученика', default=kwargs['class_num'])
        class_letter = StringField('Литера класса ученика', default=kwargs['class_letter'])
        submit = SubmitField('Искать')

    return StudentFilterForm()


class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(max=128)])
    confirm_new_password = PasswordField('Повторите пароль', validators=[EqualTo('new_password')])
    submit = SubmitField('Сменить пароль')


def give_book_form(students):
    class GiveBookForm(FlaskForm):
        select_student = SelectField("Выберите, кому дать эту книгу", choices=[(str(st.id), st.surname + ' ' + st.name) for st in students])
        submit = SubmitField("Отправить")
    return GiveBookForm()


class JoinLibraryForm(FlaskForm):
    id = StringField("Идентификатор библиотеки", validators=[DataRequired()])
    submit = SubmitField('Присоединиться')


def edit_student_profile_form(**kwargs):
    class EditStudentProfileForm(FlaskForm):
        name = StringField('Ваше имя', default=kwargs['name'])
        surname = StringField('Ваша фамилия', default=kwargs['surname'])
        submit = SubmitField('Изменить')
    return EditStudentProfileForm()

