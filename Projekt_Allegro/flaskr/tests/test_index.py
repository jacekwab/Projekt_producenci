import pytest
import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flaskr.main import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    """Test the home route."""
    response = client.get('/')
    assert response.status_code == 200


def test_data_display_post_valid_phrase(client):
    """Test the /results route with a valid input."""
    response = client.post('/results', data={'phrase': 'valid input'})
    assert response.status_code == 200


def test_data_display_post_empty_phrase(client):
    rv = client.post('/', data={'phrase': '  '})
    assert rv.status_code == 405  # Sprawdza, czy nie ma możliwości przekierowania
    assert rv.location is None  # Sprawdza, czy nie ma przekierowania na żadną stronę


def test_data_display_post_special_characters(client):
    """Test the /results route with a phrase containing special characters."""
    special_characters_phrase = '!@#$%^&*()_+{}:"<>?[];\',./`~'
    response = client.post('/results', data={'phrase': special_characters_phrase})
    assert response.status_code == 200

def test_data_display_random_phrase(client):
    """Test the /results route with a random "word" containing
    two or more character syllables (the polish alphabet characters)."""
    from tests.auxilary_test_functions import random_word_between_1_20_chars
    randomised_phrase = random_word_between_1_20_chars()
    response = client.post('/results', data={'phrase': randomised_phrase})
    assert response.status_code == 200