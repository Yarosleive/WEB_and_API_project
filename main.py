from flask import Flask, url_for, request, render_template, redirect, session, abort, make_response, jsonify
from data import db_session, api
from data.users import User
from data.films import Films
from flask_login import LoginManager, login_required, current_user
from flask_login import LoginManager, login_user, logout_user
from forms.user import RegisterForm, LoginForm, FilmForm
from re import sub
import sqlite3
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/img'


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/')
def index():
    db_sess = db_session.create_session()
    films = db_sess.query(Films)
    return render_template("index.html", films=films)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            is_admin = False
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/film', methods=['GET', 'POST'])
@login_required
def film():
    form = FilmForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        logo_dir = os.path.join(os.path.dirname(app.instance_path), 'static')
        f = form.logo.data
        filename = secure_filename(f.filename)
        f.save(os.path.join(logo_dir, 'img', filename))
        film = Films(
            name = form.name.data,
            genre = form.genre.data,
            year = form.year.data,
            director = form.director.data,
            rating = form.rating.data,
            logo = filename
            )
        current_user.film.append(film)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    print(form.validate_on_submit())
    return render_template('film.html', title='Добавить работу', form=form)

@app.route('/film/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = FilmForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        film = db_sess.query(Films).filter(Films.id == id, current_user.is_admin).first()
        if film:
            form.name.data = film.name 
            form.genre.data = film.genre 
            form.year.data = film.year 
            form.director.data = film.director 
            form.rating.data = film.rating 
            logo_path = os.path.join(os.path.dirname(app.instance_path), 'static\\img\\' + film.logo)
            with open(logo_path, 'r') as f:
                form.logo.data = f
            print(logo_path)
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        film = db_sess.query(Films).filter(Films.id == id, current_user.is_admin).first()
        if film:
            os.remove('static\\img\\' + film.logo)
            logo_dir = os.path.join(os.path.dirname(app.instance_path), 'static')
            f = form.logo.data
            filename = secure_filename(f.filename)
            f.save(os.path.join(logo_dir, 'img', filename))
            film.name = form.name.data
            film.genre = form.genre.data
            film.year = form.year.data
            film.director = form.director.data
            film.rating = form.rating.data
            film.logo = filename
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    
    return render_template('film.html',
                           title='Редактирование работы',
                           logo_path = '..\\static\\img\\' + film.logo,
                           form=form
                           )

@app.route('/film_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def film_delete(id):
    db_sess = db_session.create_session()
    film = db_sess.query(Films).filter(Films.id == id,
                                      (Films.user == current_user)|(current_user == '1')
                                      ).first()
    if film:
        logo_path = os.path.join(os.path.dirname(app.instance_path), 'static\\img\\' + film.logo)
        os.remove(logo_path)
        db_sess.delete(film)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


def main():
    db_session.global_init("db/films.sqlite")
#     con = sqlite3.connect('db/films-catalog.sqlite')
#     cur = con.cursor()
#     db_sess = db_session.create_session()
#     result = cur.execute("""
#         SELECT id, name, genre, year, director, rating, logo FROM films
#     """).fetchall()
#     for elem in result:
#         film = Films()
#         film.id = elem[0]
#         film.name = elem[1]
#         film.genre = elem[2]
#         film.year = elem[3]
#         film.director = elem[4]
#         film.rating = elem[5]
#         film.logo = sub('film-catalog/pictures/', '', elem[6])
#         film.user_id = 1
#         db_sess.add(film)
#         db_sess.commit()
#     user = db_sess.query(User).filter(User.id == 1).first()
#     user.is_admin = True
#     db_sess.commit()
    app.register_blueprint(api.blueprint)
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
   main()