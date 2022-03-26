import flask_login
from flask import render_template, Flask
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.utils import redirect
from data.books import Books

from data import db_session
from data.users import User

import os
from PIL import Image

from login_form import LoginForm
from register_form import RegisterForm
from books_form import BooksForm
from edit_book_form import EditBookForm

login_manager = LoginManager()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager.init_app(app)

db_session.global_init("db/books.db")

DEFAULT_IMAGE_TITLE = 'static/img/title.jpg'


def save_image(size, file, filename):
    im = Image.open(file)
    im = im.resize((size))
    im.save(filename)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


def timedelta_to_hms(duration):
    # преобразование в часы, минуты и секунды
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return hours, minutes, seconds


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('auto.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('auto.html', title='Авторизация', form=form)


@app.route('/addbook', methods=['GET', 'POST'])
def addbook():
    if not flask_login.current_user.is_authenticated:
        return redirect("/")
    form = BooksForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        book = Books()
        book.user_id = flask_login.current_user.id
        book.name = form.data['name']
        book.author = form.data['author']
        book.description = form.data['description']
        filename = form.path_image_title.data.filename
        if len(filename) == 0:
            filename = DEFAULT_IMAGE_TITLE
            book.path_image_title = filename
        else:
            book.path_image_title = 'static/img/' + \
                                    str(flask_login.current_user.id) + \
                                    '/' + filename
            if not os.path.isdir('static/img/' +
                                 str(flask_login.current_user.id)):
                os.mkdir('static/img/' + str(flask_login.current_user.id))
            save_image((256, 256), form.path_image_title.data,
                       book.path_image_title)
        book.is_finished = form.data['isfin']
        session.add(book)
        session.commit()
        return redirect("/")
    return render_template('addbooks.html', form=form,
                           title_image=DEFAULT_IMAGE_TITLE)


@app.route('/')
def index():
    rs = []
    session = db_session.create_session()
    for books in session.query(Books):
        d = dict()
        user = session.query(User).filter(User.id == books.user_id).first()
        d['title'] = books.name
        d['author'] = books.author
        d['name'] = user.surname + ' ' + user.name
        d['description'] = books.description
        d['user_id'] = books.user_id
        d['id_book'] = books.id
        if books.is_finished:
            d['finished'] = 'Finished'
        else:
            d['finished'] = 'Is not finished'
        d['path_image_title'] = books.path_image_title
        rs.append(d)
    return render_template('index.html',
                           header='Мои книги',
                           param=rs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = User()
        user.surname = form.data['surname']
        user.name = form.data['name']
        user.email = form.data['login']
        user.hashed_password = form.data['passw']
        session.add(user)
        session.commit()
        return redirect('/')
    return render_template('form.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/editbook/<id_book>', methods=['GET', 'POST'])
def editbook(id_book):
    session = db_session.create_session()
    if not flask_login.current_user.is_authenticated:
        return redirect("/")
    form = EditBookForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        book = session.query(Books).filter(Books.id == id_book).first()
        book.user_id = flask_login.current_user.id
        book.name = form.data['name']
        book.author = form.data['author']
        book.description = form.data['description']
        book.is_finished = form.data['isfin']
        filename = form.path_image_title.data.filename
        if len(filename) != 0:
            book.path_image_title = 'static/img/' + \
                                    str(flask_login.current_user.id) + \
                                    '/' + filename
            if not os.path.isdir('static/img/' +
                                 str(flask_login.current_user.id)):
                os.mkdir('static/img/' + str(flask_login.current_user.id))
            save_image((192, 256), form.path_image_title.data,
                       book.path_image_title)
        session.commit()
        return redirect("/")
    book = session.query(Books).filter(Books.id == id_book).first()
    form.name.data = book.name
    form.author.data = book.author
    form.description.data = book.description
    form.isfin.data = book.is_finished
    return render_template('editbooks.html', form=form,
                           title_image=book.path_image_title)


@app.route('/delbook/<id_book>', methods=['GET', 'POST'])
def delbook(id_book):
    session = db_session.create_session()
    if not flask_login.current_user.is_authenticated:
        return redirect("/")
    user = session.query(User).filter(User.id == flask_login.current_user.id).first()
    session = db_session.create_session()
    book = session.query(Books).filter(Books.id == id_book).first()
    if user.id == 1 or user.id == book.user_id:
        session.delete(book)
        session.commit()
    return redirect("/")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
