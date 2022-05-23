from flask import Flask, g
from flask import render_template
import os
import sqlite3
from datetime import datetime
from flask import flash, redirect, url_for, request
from flask import session

app = Flask(__name__)

app.config.update(dict(
    SECRET_KEY='bardzosekretnawartosc',
    DATABASE=os.path.join(app.root_path, 'zadania.db'),
    SITE_NAME='Moje zadania'
))


def get_db():
    """Funkcja tworząca połączenie z bazą danych"""
    if not g.get('db'):  # jeżeli brak połączenia, to je tworzymy
        con = sqlite3.connect(app.config['DATABASE'])
        con.row_factory = sqlite3.Row
        g.db = con  # zapisujemy połączenie w kontekście aplikacji
    return g.db  # zwracamy połączenie z bazą


@app.teardown_appcontext
def close_db(error):
    """Zamykanie połączenia z bazą"""
    if g.get('db'):
        g.db.close()


@app.route('/')
def index():
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
            db.execute('INSERT INTO zadania VALUES (?, ?, ?, ?);',
                       [None, zadanie, zrobione, data_pub])
            db.commit()
            flash('Dodano nowe zadanie.')
            return redirect(url_for('zadania'))

        error = 'Nie możesz dodać pustego zadania!'  # komunikat o błędzie
    if 'id' in session:
        db = get_db()
        kursor = db.execute('SELECT * FROM zadania ORDER BY data_pub DESC;')
        zadania = kursor.fetchall()
        return render_template('zadania_lista.html', zadania=zadania, error=error)
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


@app.route('/loguj', methods=['GET', 'POST'])
def loguj():
    if request.method == 'POST':
        # przesłanie formularza
        email = request.form['email']
        db = get_db()
        kursor = db.execute('SELECT * FROM users WHERE email=?', [email])
        id_user = kursor.fetchone()
        if id_user is None:
            # tworzenie konta
            db.execute('INSERT INTO users VALUES (?, ?)', [None, email])
            db.commit()
            flash(f'Utworzono konto {email}')
            id_user = kursor.lastrowid
        else:
            id_user = id_user[0]
        session['id'] = id_user
        session['email'] = email
        return redirect(url_for('zadania'))
    return render_template('loguj.html')


@app.route('/wyloguj')
def wyloguj():
    flash(f"Wylogowano użytkownika {session['email']}.")
    session.pop('id', default=None)
    session.pop('email', default=None)
    return redirect(url_for('index'))


app.run(debug=True)
