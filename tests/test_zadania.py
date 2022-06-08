import pytest
from todor.db import get_db


def test_index(client, auth):
    response = client.get('/')
    assert b"Zaloguj się" in response.data
    assert b"Utwórz konto" in response.data

    auth.login()
    response = client.get('/')
    assert b'Wyloguj się' in response.data
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
