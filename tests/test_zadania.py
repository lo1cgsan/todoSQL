import pytest
from todor.db import get_db


def test_index(client, auth):
    response = client.get('/')
    assert b"Zaloguj się" in response.data
    assert b"Utwórz konto" in response.data

    auth.login()
    response = client.get('/')
    assert b'Wyloguj się' in response.data
    assert b'test' in response.data
    assert b'by test on 2018-01-01' in response.data
    assert b'test\nbody' in response.data
    assert b'href="/1/update"' in response.data
