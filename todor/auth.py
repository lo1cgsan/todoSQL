import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from todor.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        haslo = request.form['haslo']
        db = get_db()
        error = None

        if not email:
            error = 'Email jest wymagany.'
        elif not haslo:
            error = 'Hasło jest wymagane.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO users (email, haslo) VALUES (?, ?)",
                    (email, generate_password_hash(haslo)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"Adres {email} jest już zarejestrowany."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        haslo = request.form['haslo']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()

        if user is None:
            error = 'Błędny email.'
        elif not check_password_hash(user['haslo'], haslo):
            error = 'Błędne hasło.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


# funkcja, która uruchamia się przed każdym widokiem
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# dekorator, który sprawdza, czy użytkownik jest zalogowany
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
