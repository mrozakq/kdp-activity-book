import os
import sys

import pytest

# Ensure dashboard_kdp/ is importable when pytest is run from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_index(client):
    r = client.get('/')
    assert r.status_code == 200


def test_history(client):
    r = client.get('/history')
    assert r.status_code == 200


def test_kdp_hub(client):
    r = client.get('/kdp')
    assert r.status_code == 200


def test_kdp_coloring(client):
    r = client.get('/kdp/coloring')
    assert r.status_code == 200


def test_kdp_flashcard(client):
    r = client.get('/kdp/flashcard')
    assert r.status_code == 200


def test_kdp_cover(client):
    r = client.get('/kdp/cover')
    assert r.status_code == 200


def test_kdp_builder(client):
    r = client.get('/kdp/builder')
    assert r.status_code == 200


def test_kdp_activity(client):
    r = client.get('/kdp/activity')
    assert r.status_code == 200


def test_sample_coloring(client):
    r = client.get('/sample/coloring')
    assert r.status_code == 200
    assert b'quote' in r.data


def test_sample_flashcard(client):
    r = client.get('/sample/flashcard')
    assert r.status_code == 200
    assert b'text_top' in r.data
