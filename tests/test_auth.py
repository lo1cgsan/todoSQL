import pytest
from flask import g, session
from todor.db import get_db


def test_register(client, app):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'email': 'a', 'haslo': 'a'}
    )
    assert response.headers["Location"] == "/auth/login"

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM users WHERE email = 'a'",
        ).fetchone() is not None


@pytest.mark.parametrize(('email', 'haslo', 'message'), (
    ('', '', 'Email jest wymagany.'),
    ('a', '', 'Hasło jest wymagane.'),
    ('adres1@wp.pl', 'test', 'już zarejestrowany'),
))
def test_register_validate_input(client, email, haslo, message):
    response = client.post(
        '/auth/register',
        data={'email': email, 'haslo': haslo}
    )
    assert message in response.get_data(as_text=True)


def test_login(client, auth):
    assert client.get('/auth/login').status_code == 200
    response = auth.login()
    assert response.headers["Location"] == "/"

    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['email'] == 'adres1@wp.pl'


@pytest.mark.parametrize(('email', 'haslo', 'message'), (
    ('a', 'test', 'Błędny email.'),
    ('adres1@wp.pl', 'a', 'Błędne hasło.'),
))
def test_login_validate_input(auth, email, haslo, message):
    response = auth.login(email, haslo)
    assert message in response.get_data(as_text=True)


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session
