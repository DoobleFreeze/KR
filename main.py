# Испорт функций для основой работы сайта
from flask import Flask, render_template, redirect, request, make_response, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_ngrok import run_with_ngrok
# Импорт функций (Классов) для работы с базой данных
from data import db_session
from data.users import User
from data.news import News
# Импорт классов форм для заполненя данными пользователем
from registerform import RegisterForm
from loginform import LoginForm
from newsform import NewsForm

# Операции для запуска сайта
app = Flask(__name__)
run_with_ngrok(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'rtu_mirea_ona_key'  # Ключ для хеширования паролей


@login_manager.user_loader
def load_user(user_id):  # Возвращает информацию о пользователе по его ID
    s = db_session.create_session()
    return s.query(User).get(user_id)


def main():
    db_session.global_init("db/blogs.sqlite")  # Открывает базу данных
    app.run()  # Запускает сайт


@app.route("/")
def index():
    return render_template('index.html', title='Post.')


@app.route("/posts")
def posts():
    session = db_session.create_session()
    news = session.query(News)
    s = []
    for i in news:
        x = [i.title, i.content, i.user.name, i.user]
        a = str(i.created_date).split()
        c = a[0].split('-')
        b = ':'.join(a[1].split(":")[:2]) + ' ' + "{}.{}.{}".format(c[2], c[1], c[0])
        x.append(b)
        x.append(i.is_private)
        x.append(i.id)
        s.append(x)
    sp = list(reversed(s))
    return render_template("posts.html", news=sp, title='Лента')


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        session.merge(current_user)
        session.commit()
        return redirect('/posts')
    return render_template('news.html', title='Добавление поста',
                           form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            session.commit()
            return redirect('/posts')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование поста', form=form)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == id,
                                      News.user == current_user).first()
    if news:
        session.delete(news)
        session.commit()
    else:
        abort(404)
    return redirect('/posts')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="*Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="*Такой пользователь уже есть")
        if session.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="*Это имя пользователя уже занято")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/posts")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    main()
