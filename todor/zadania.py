from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from todor.auth import login_required
from todor.db import get_db

bp = Blueprint('zadania', __name__)

@bp.route('/')
def index():
    db = get_db()
    zadania = db.execute(
        'SELECT z.id, zadanie, zrobione, data_pub, id_user, email'
        ' FROM zadania z JOIN users u ON z.id_user = u.id'
        ' ORDER BY data_pub DESC'
    ).fetchall()
    return render_template('zadania/index.html', zadania=zadania)


@bp.route('/dodaj', methods=('GET', 'POST'))
@login_required
def dodaj():
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
                'INSERT INTO zadania (id_user, zadanie)'
                ' VALUES (?, ?)',
                (g.user['id'], zadanie)
            )
            db.commit()
            return redirect(url_for('zadania.index'))

    return render_template('zadania/dodaj.html')


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


@bp.route('/<int:id>/edytuj', methods=('GET', 'POST'))
@login_required
def edytuj(id):
    zadanie = get_zadanie(id)

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
            return redirect(url_for('zadania.index'))

    return render_template('zadania/edytuj.html', zadanie=zadanie)


@bp.route('/<int:id>/usun', methods=('POST',))
@login_required
def usun(id):
    get_zadanie(id)
    db = get_db()
    db.execute('DELETE FROM zadania WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('zadania.index'))


@bp.route('/<int:id>/<int:status>/zmien_status', methods=('POST',))
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
    return redirect(url_for('zadania.index'))
