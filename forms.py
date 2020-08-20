from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, BooleanField, TextAreaField, DateTimeField, \
    DateField, TimeField, FileField, IntegerField, SelectField
from wtforms.fields.html5 import EmailField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.recaptcha import RecaptchaField
from datetime import datetime


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
    library_id = StringField('Идентификатор библтотеки (спросите у библиотекаря)', validators=[DataRequired(),
                                                                                               NumberRange(min=1, max=11)])
    class_num = IntegerField('Номер класса, в котором вы учитесь', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Адрес электронной почты')
    password = PasswordField('Пароль')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class BorrowBookForm(FlaskForm):
    submit = SubmitField('Взять книгу')


def book_filter_form(**kwargs):
    class BookFilterForm(FlaskForm):
        id = IntegerField('Номер книги', default=kwargs['id'])
        name = StringField('Название книги', default=kwargs['name'])
        author = StringField('Фамилия автора', default=kwargs['author'])
        publication_year = IntegerField('Год публикации', default=kwargs['publication_year'])
        edition_id = IntegerField('Номер издания', default=kwargs['edition_id'])
        owner_id = IntegerField('Номер владельца', default=kwargs['owner_id'])
        owner_surname = StringField('Фамилия владельца', default=kwargs['owner_surname'])
        submit = SubmitField('Искать')

    return BookFilterForm()


def edition_filter_form(**kwargs):
    class EditionFilterForm(FlaskForm):
        id = StringField('Номер издания', default=kwargs['id'])
        name = StringField('Название книги', default=kwargs['name'])
        author = StringField('Фамилия автора', default=kwargs['author'])
        publication_year = StringField('Год публиукации', default=kwargs['publication_year'])
        submit = SubmitField('Искать')

    return EditionFilterForm()


def student_filter_form(**kwargs):
    class StudentFilterForm(FlaskForm):
        id = IntegerField('Номер ученика', default=kwargs['id'])
        surname = StringField('Фамилия ученика', default=kwargs['surname'])
        class_num = IntegerField('Номер класса ученика', default=kwargs['class_num'])
        submit = SubmitField('Искать')

    return StudentFilterForm()


