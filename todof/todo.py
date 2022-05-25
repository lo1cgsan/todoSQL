from flask import Flask, g
from flask import render_template
import os
import sqlite3
import click
from flask import current_app
from flask.cli import with_appcontext
from datetime import datetime
from flask import flash, redirect, url_for, request
from flask import session
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash


app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.root_path, 'zadania.db'),
    SITE_NAME='Moje zadania'
)

def get_db():
    """Funkcja tworząca połączenie z bazą danych"""
    if not g.get('db'):  # jeżeli brak połączenia, to je tworzymy
        # zapisujemy połączenie w kontekście aplikacji
        g.db = sqlite3.connect(app.config['DATABASE'])
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


# @click.command('init-db')
# @with_appcontext
# def init_db_command():
#     """Usunięcie danych i utworzenie nowych tabel."""
#     init_db()
#     click.echo('Inicjacja bazy danych.')

# app.cli.add_command(init_db_command)

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
        kursor = db.execute('SELECT * FROM zadania ORDER BY data_pub DESC;')
        zadania = kursor.fetchall()
        return render_template('zadania_lista.html', zadania=zadania, error=error)
    else:
        flash('Dodawanie zadań wymaga logowania.')
        return redirect(url_for('loguj'))


@app.route('/zrobione', methods=['POST'])
def zrobione():
    """Zmiana statusu zadania na wykonane."""
    zadanie_id = request.form['id']
    db = get_db()
    db.execute('UPDATE zadania SET zrobione=1 WHERE id=?', [zadanie_id])
    db.commit()
    flash('Zmieniono status zadania.')
    return redirect(url_for('zadania'))


@app.route('/niezrobione', methods=['POST'])
def niezrobione():
    """Zmiana statusu zadania na wykonane."""
    zadanie_id = request.form['id']
    db = get_db()
    db.execute('UPDATE zadania SET zrobione=0 WHERE id=?', [zadanie_id])
    db.commit()
    flash('Zmieniono status zadania.')
    return redirect(url_for('zadania'))


@app.route('/rejestruj', methods=['GET', 'POST'])
def loguj():
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
            error = "Błędne hasło."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for('zadania'))
    flash(error)
    return render_template('loguj.html')


@app.route('/wyloguj')
def wyloguj():
    flash(f"Wylogowano użytkownika {session['email']}.")
    session.clear()
    return redirect(url_for('index'))


with app.app_context():
    if not os.path.exists(current_app.config['DATABASE']):
        init_db()
    app.run(debug=True)
