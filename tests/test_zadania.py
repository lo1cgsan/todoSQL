import pytest
from todor.db import get_db


def test_index(client, auth):
    response = client.get('/')
    assert "Zaloguj się" in response.get_data(as_text=True)
    assert "Utwórz konto" in response.get_data(as_text=True)

    auth.login()
    response = client.get('/')
    assert 'Wyloguj się' in response.get_data(as_text=True)
    assert b'adres1@wp.pl' in response.data
    assert b'2018-01-01' in response.data
    assert b'test\nbody' in response.data
    assert b'href="/1/edytuj"' in response.data


@pytest.mark.parametrize('path', (
    '/dodaj',
    '/1/edytuj',
    '/1/usun',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE zadania SET id_user = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post('/1/edytuj').status_code == 403
    assert client.post('/1/usun').status_code == 403
    # current user doesn't see edit link
    assert b'href="/1/edytuj"' not in client.get('/').data


@pytest.mark.parametrize('path', (
    '/2/edytuj',
    '/2/usun',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get('/dodaj').status_code == 200
    client.post('/dodaj', data={'zadanie': 'nowe'})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM zadania').fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get('/1/edytuj').status_code == 200
    client.post('/1/edytuj', data={'zadanie': 'poprawione'})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM zadania WHERE id = 1').fetchone()
        assert post['zadanie'] == 'poprawione'


@pytest.mark.parametrize('path', (
    '/dodaj',
    '/1/edytuj',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'zadanie': '', 'id': 1})
    assert 'Zadanie nie może być puste.' in response.get_data(as_text=True)


def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/usun')
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        zadanie = db.execute('SELECT * FROM zadania WHERE id = 1').fetchone()
        assert zadanie is None
