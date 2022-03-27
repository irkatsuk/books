import flask_login
from flask import render_template, Flask
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.utils import redirect

from data import db_session
from data.users import User
from data.books import Books
from data.review import Review

import os
from PIL import Image
import difflib

from login_form import LoginForm
from register_form import RegisterForm
from books_form import BooksForm
from edit_book_form import EditBookForm
from review_form import ReviewForm

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


def add_similar_reviews(id_book, title, author, rs):
    session = db_session.create_session()
    books = session.query(Books)
    ids = []
    titles = []
    authors = []
    for book in books:
        if book.id == int(id_book):
            continue
        ids.append(book.id)
        titles.append(book.name)
        authors.append(book.author)
    match_titles = difflib.get_close_matches(title, titles, cutoff=0.7, n=10)
    match_authors = difflib.get_close_matches(author, authors, cutoff=0.3, n=10)
    is_find = False
    for i in range(len(ids)):
        t = titles[i]
        a = authors[i]
        if t in match_titles and a in match_authors:
            rw = session.query(Review).filter(Review.book_id == ids[i]).first()
            if rw is not None:
                d = dict()
                d['title'] = t
                d['author'] = a
                d['description'] = rw.description
                rs.append(d)
                is_find = True
    return is_find


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


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


def index_for_auth_users():
    rs = []
    session = db_session.create_session()
    for books in session.query(Books):
        if books.user_id != flask_login.current_user.id:
            continue
        user = session.query(User).filter(User.id == books.user_id).first()
        review = session.query(Review).filter(Review.book_id == books.id).first()
        curr_review = session.query(Review). \
            filter(Review.book_id == books.id,
                   Review.user_id == flask_login.current_user.id).first()
        d = dict()
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
        if review is not None:
            d['review'] = 'yes'
        else:
            d['review'] = 'no'
        if curr_review is not None:
            d['curr_review'] = 'yes'
        rs.append(d)
    return render_template('index.html', header='Мои книги', param=rs)


def index_for_unknown_users():
    rs = []
    session = db_session.create_session()
    for books in session.query(Books):
        review = session.query(Review).filter(Review.book_id == books.id).first()
        d = dict()
        d['title'] = books.name
        d['author'] = books.author
        d['description'] = books.description
        d['id_book'] = books.id
        if review is not None:
            d['review'] = 'yes'
        else:
            reviews = []
            if add_similar_reviews(books.id, books.name, books.author, reviews):
                d['review'] = 'yes'
            else:
                d['review'] = 'no'
        rs.append(d)
    return render_template('lightindex.html', header='Книги', param=rs)


@app.route('/')
def index():
    if flask_login.current_user.is_authenticated:
        return index_for_auth_users()
    return index_for_unknown_users()


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
    review = session.query(Review). \
        filter(Review.user_id == flask_login.current_user.id,
               Review.book_id == id_book).first()
    if review is not None:
        session.delete(review)
        session.commit()
    user = session.query(User).filter(User.id == flask_login.current_user.id).first()
    session = db_session.create_session()
    book = session.query(Books).filter(Books.id == id_book).first()
    if user.id == book.user_id:
        session.delete(book)
        session.commit()
    return redirect("/")


@app.route('/editreview/<id_book>', methods=['GET', 'POST'])
def editreview(id_book):
    if not flask_login.current_user.is_authenticated:
        return redirect("/")
    session = db_session.create_session()
    review = session.query(Review). \
        filter(Review.user_id == flask_login.current_user.id,
               Review.book_id == id_book).first()
    form = ReviewForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        review = session.query(Review). \
            filter(Review.user_id == flask_login.current_user.id,
                   Review.book_id == id_book).first()
        if review is None:
            review = Review()
            review.user_id = flask_login.current_user.id
            review.book_id = id_book
            review.description = form.data['description']
            session.add(review)
        else:
            review.description = form.data['description']
        session.commit()
        return redirect("/")
    if review is not None:
        form.description.data = review.description
    return render_template('editreview.html', form=form)


@app.route('/delreview/<id_book>', methods=['GET', 'POST'])
def delreview(id_book):
    if not flask_login.current_user.is_authenticated:
        return redirect("/")
    session = db_session.create_session()
    review = session.query(Review). \
        filter(Review.user_id == flask_login.current_user.id,
               Review.book_id == id_book).first()
    if review is not None:
        session.delete(review)
        session.commit()
    return redirect("/")


@app.route('/review/<id_book>', methods=['GET'])
def review(id_book):
    rs = []
    session = db_session.create_session()
    book = session.query(Books).filter(Books.id == id_book).first()
    title = book.name
    author = book.author
    reviews = session.query(Review).filter(Review.book_id == id_book)
    for review in reviews:
        d = dict()
        d['title'] = book.name
        d['author'] = book.author
        d['description'] = review.description
        rs.append(d)
    add_similar_reviews(id_book, title, author, rs)
    return render_template('review.html', header='Рецензии', param=rs)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
