from flask import Flask, g
from flask import render_template
import os
import sqlite3
from flask import current_app
import functools
from datetime import datetime
from flask import flash, redirect, url_for, request
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.root_path, 'zadania.db'),
    SITE_NAME='Moje zadania'
)

def get_db():
    """Funkcja tworząca połączenie z bazą danych"""
    if 'db' not in g:  # jeżeli brak połączenia, to je tworzymy
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )  # tworzymy i zapisujemy połączenie w kontekście aplikacji
        g.db.row_factory = sqlite3.Row
    return g.db  # zwracamy połączenie z bazą


@app.teardown_appcontext
def close_db(error):
    """Zamykanie połączenia z bazą"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Czyszczenie bazy i utworzenie jej na nowo."""
    db = get_db()

    with current_app.open_resource('baza.sql') as f:
        db.executescript(f.read().decode('utf8'))


@app.route('/')
def index():
    print(session)
    return render_template('index.html')


@app.route('/zadania', methods=['GET', 'POST'])
def zadania():
    error = None
    if request.method == 'POST':
        zadanie = request.form['zadanie'].strip()
        if len(zadanie) > 0:
            zrobione = '0'
            data_pub = datetime.now()
            db = get_db()
            db.execute('INSERT INTO zadania VALUES (?, ?, ?, ?, ?);',
                       [None, session["user_id"], zadanie, zrobione, data_pub])
            db.commit()
            flash('Dodano nowe zadanie.')
            return redirect(url_for('zadania'))

        error = 'Nie możesz dodać pustego zadania!'  # komunikat o błędzie
    if "user_id" in session:
        db = get_db()
        zadania = db.execute('SELECT * FROM zadania ORDER BY data_pub DESC').fetchall()
        return render_template('zadania_lista.html', zadania=zadania, error=error)
    else:
        flash('Dodawanie zadań wymaga logowania.')
        return redirect(url_for('loguj'))


@app.route('/rejestruj', methods=['GET', 'POST'])
def rejestruj():
    if request.method == 'POST':
        email = request.form['email'].strip()
        haslo = request.form['haslo'].strip()

        db = get_db()
        error = None

        try:
            # tworzenie konta
            db.execute(
                'INSERT INTO users VALUES (?, ?, ?)',
                [None, email, generate_password_hash(haslo)]
            )
            db.commit()
        except db.IntegrityError:
            error = f"Użytkownik {email} jest już zarejestrowany."
        else:
            flash(f'Utworzono konto {email}')
            return redirect(url_for('loguj'))
        flash(error)
    return render_template('rejestruj.html')


@app.route('/loguj', methods=['GET', 'POST'])
def loguj():
    if request.method == 'POST':
        # przesłanie formularza
        email = request.form['email'].strip()
        haslo = request.form['haslo'].strip()

        db = get_db()
        error = None

        user = db.execute('SELECT * FROM users WHERE email = ?', [email]).fetchone()

        if user is None:
            # tworzenie konta
            error = "Błędny email."
        elif not check_password_hash(user["haslo"], haslo):
            print(user['haslo'])
            print(generate_password_hash(haslo))
            error = "Błędne hasło."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for('zadania'))
        flash(error)
    return render_template('loguj.html')


# funkcja, która uruchamia się przed każdym widokiem
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()


@app.route('/wyloguj')
def wyloguj():
    flash(f"Wylogowano użytkownika {session['email']}.")
    session.clear()
    return redirect(url_for('index'))


# dekorator, który sprawdza, czy użytkownik jest zalogowany
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('loguj'))

        return view(**kwargs)

    return wrapped_view


def get_zadanie(id, check_author=True):
    zadanie = get_db().execute(
        'SELECT z.id, zadanie, zrobione, data_pub, id_user, email'
        ' FROM zadania z JOIN users u ON z.id_user = u.id'
        ' WHERE z.id = ?',
        (id,)
    ).fetchone()

    if zadanie is None:
        abort(404, f"Zadanie id {id} nie istnieje.")

    if check_author and zadanie['id_user'] != g.user['id']:
        abort(403)

    return zadanie


@app.route('/<int:id>/edytuj', methods=('GET', 'POST'))
@login_required
def edytuj(id):
    zadanie = get_zadanie(id)
    print(zadanie['zadanie'])
    if request.method == 'POST':
        zadanie = request.form['zadanie']
        error = None

        if not zadanie:
            error = 'Treść zadania nie może być pusta.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE zadania SET zadanie = ?'
                ' WHERE id = ?',
                (zadanie, id)
            )
            db.commit()
            return redirect(url_for('index'))

    return render_template('edytuj.html', zadanie=zadanie)


@app.route('/<int:id>/usun', methods=('POST',))
@login_required
def usun(id):
    get_zadanie(id)
    db = get_db()
    db.execute('DELETE FROM zadania WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('index'))


@app.route('/<int:id>/<int:status>/zmien_status', methods=('POST',))
@login_required
def zmien_status(id, status):
    get_zadanie(id)
    db = get_db()
    db.execute(
        'UPDATE zadania SET zrobione = ?'
        ' WHERE id = ?',
        (status, id)
    )
    db.commit()
    return redirect(url_for('zadania'))


with app.app_context():
    if not os.path.exists(current_app.config['DATABASE']):
        init_db()
    app.run(debug=True)
