import pytest
import sys
import os
import requests
import socket

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
    response = client.post('/results', data={'phrase': '  '})
    assert response.status_code == 302  # Sprawdza, czy nie ma możliwości przekierowania
    assert response.location is '/'  # Sprawdza, czy przekierunkowanie jest na stronę główną


def test_data_display_invalid_token(client, mocker):
    """Test obsługi nieprawidłowego tokena (401)."""

    # Tworzymy sztuczną odpowiedź API z kodem 401 (Unauthorized)
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mocker.Mock(status_code=401))

    # Mockujemy requests.get, aby zwracało naszą sztuczną odpowiedź
    mocker.patch('requests.get', return_value=mock_response)

    response = client.post('/results', data={'phrase': 'valid input'})

    # Sprawdzamy, czy błąd został obsłużony
    assert response.status_code == 302


# Blokujemy połączenia sieciowe, aby zasymulować brak internetu
class NoInternet:
    def __enter__(self):
        self.original_socket = socket.socket
        socket.socket = lambda *args, **kwargs: None  # Blokujemy tworzenie gniazda

    def __exit__(self, exc_type, exc_value, traceback):
        socket.socket = self.original_socket  # Przywracamy działanie sieci


def test_no_internet_connection_on_results_page(client):
    """Test sprawdzający obsługę błędu braku internetu na stronie /results."""

    with NoInternet():  # Symulujemy brak internetu
        response = client.post('/results', data={'phrase': 'test'})
    # Sprawdzamy, czy użytkownik NIE został przekierowany
    assert response.status_code == 200  # Powinna zostać wyrenderowana strona wyników


def test_data_display_post_too_long_phrase(client):
    """Test the /results route with an invalid (too long) input."""
    long_phrase = 'a' * 2001  #Przykład za długiej frazy
    response = client.post('/results', data={'phrase': long_phrase})
    assert response.status_code == 302  #sprawdzić co się stanie
    assert response.location is '/'


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
