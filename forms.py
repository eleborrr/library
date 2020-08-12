from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, BooleanField, TextAreaField, DateTimeField, \
    DateField, TimeField, FileField, IntegerField, SelectField
from wtforms.fields.html5 import EmailField, DateTimeLocalField
from wtforms.validators import DataRequired, Length
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
    library_id = StringField('Идентификатор библтотеки (спросите у библиотекаря)', validators=[DataRequired()])
    class_num = IntegerField('Номер класса, в котором вы учитесь', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Адрес электронной почты')
    password = PasswordField('Пароль')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


