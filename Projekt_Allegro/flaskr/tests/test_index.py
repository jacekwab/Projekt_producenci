import pytest
import sys
import os
import requests
import socket

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flaskr.main import app
from unittest.mock import patch, Mock


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

    response = client.get('/')

    # Sprawdzamy, czy błąd został obsłużony
    assert response.status_code == 200


# Blokujemy połączenia sieciowe, aby zasymulować brak internetu
class NoInternet:
    def __enter__(self):
        self.original_socket = socket.socket
        socket.socket = lambda *args, **kwargs: None  # Blokujemy tworzenie gniazda

    def __exit__(self, exc_type, exc_value, traceback):
        socket.socket = self.original_socket  # Przywracamy działanie sieci


def test_no_internet_connection_on_results_page(client):
    """Test sprawdzający obsługę błędu braku internetu na stronie /results.
    TODO: Do potencjalnego sprawdzenia, jakie będzie zachowanie testu na serwerze zdalnym aplikacji."""

    with NoInternet():  # Symulujemy brak internetu
        response = client.post('/results', data={'phrase': 'test'})
    # 2025-02-12 14:24:48: Sprawdzamy, czy użytkownik został przekierowany - rezygnujemy z pozostawiania dotychczasowych
    # wyników użytkownika - przekierowujemy go na główną stronę, jeśli wydarzy się błąd połączenia z serwerami
    # niewyłapany przez obsługę błędów javascripta.
    assert response.status_code == 302  # 2025-02-12: Połączenie z zewnętrznym serwerem jest nieudane.
    # Serwer deweoperski przekierowuje przepływ na stronę główną.


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


def test_success_check_connection(client):
    """Tests whether json is properly returned if the attempt to connect to the application and use it is successful."""
    response = client.get('/check_connection')
    response_json = response.get_json()
    assert response_json == {'success': True}
    assert response.status_code == 200


class NoInternet_2:
    def __enter__(self):
        # Mock 'requests.get' to raise a ConnectionError when called
        self.patcher = patch('requests.get', side_effect=ConnectionError("No internet connection"))
        self.patcher.start()

    def __exit__(self, exc_type, exc_value, traceback):
        # Stop mocking 'requests.get'
        self.patcher.stop()


def test_failure_check_connection(client):
    """Tests whether json is properly returned if the attempt to connect to the application and use it
    is not successful at the first attempt - error at the first request, but connection recovers at the second attempt."""
    with NoInternet_2():  # Symulujemy brak internetu przy pierwszym zapytaniu
        response = client.get('/check_connection')
        response_json = response.get_json()
        assert response_json == {'success': True,
                                 'error_message': 'Błąd potwierdzeniem odpowiedzi serwera Allegro.'}
        assert response.status_code == 200


class NoInternet_3:
    def __enter__(self):
        # Mock the socket module to raise an error when a socket operation is attempted
        self.original_socket = socket.socket
        socket.socket = self.mock_socket

    def __exit__(self, exc_type, exc_value, traceback):
        # Restore the original socket after the test
        socket.socket = self.original_socket

    def mock_socket(self, *args, **kwargs):
        # Raise a ConnectionError when any socket method is called
        raise ConnectionError("No internet connection")

#TODO: 2025-02-12 16:19:33: Inne niż oczekiwane działanie tego testu sprawia, że nie ma
def test_alternative_failure_check_connection(client):
    """Tests whether json is properly returned if the attempt to connect to the application and use it
    is not successful - another unknown error appears."""
    with NoInternet_3():  # Symulujemy brak internetu przy pierwszym zapytaniu
        response = client.get('/check_connection')
        response_json = response.get_json()
        assert response_json == {'success': False, 'error_message': 'Wystąpił inny nieprzewidziany, nieznany błąd.'}
        assert response.status_code == 500


def test_check_connection_http_error_handling(client):
    # Mock `requests.get` to raise an `HTTPError`
    with patch('requests.get', side_effect=requests.exceptions.HTTPError("404 Not Found")), \
        patch('requests.get', side_effect=requests.exceptions.HTTPError("404 Not Found")):
        # This request will trigger the mock, raising an HTTPError
        response = client.get('/check_connection')

        response_json = response.get_json()
        assert response_json == {'success': True,
                                 'error_message':
                                     'Błąd potwierdzeniem odpowiedzi serwera Allegro.'}
        assert response.status_code == 200


def test_check_connection_unspecified_error_handling(client):
    # Mock `requests.get` to raise an `ValueError`
    with patch('requests.get', side_effect=ValueError("This is an unspecified error.")), \
        patch('requests.get', side_effect=ValueError("This is an unspecified error.")):
        # This request will trigger the mock, raising an ValueError
        response = client.get('/check_connection')


        response_json = response.get_json()
        assert response_json == {'success': False,
                                 'error_message':
                                     'Wystąpił inny nieprzewidziany, nieznany błąd.'}
        assert response.status_code == 500

def test_check_connection_forbidden_error(client):
    """Testuje obsługę błędu 403 Forbidden."""
    with patch('requests.get', side_effect=requests.exceptions.HTTPError(response=Mock(status_code=403))):
        response = client.get('/check_connection')
        response_json = response.get_json()
        assert response_json['success'] is True
        assert 'Błąd potwierdzeniem odpowiedzi serwera Allegro.' in response_json['error_message']
        assert response.status_code == 200


def test_check_connection_too_many_requests(client):
    """Testuje obsługę błędu 429 Too Many Requests."""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.headers = {'Retry-After': '2'}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

    with patch('requests.get', return_value=mock_response):
        response = client.get('/check_connection')
        response_json = response.get_json()
        assert response_json['success'] is True
        assert 'Błąd potwierdzeniem odpowiedzi serwera Allegro.' in response_json['error_message']
        assert response.status_code == 200


def test_check_connection_server_error(client):
    """Testuje obsługę błędu 500+ (błąd serwera)."""
    with patch('requests.get', side_effect=requests.exceptions.HTTPError(response=Mock(status_code=500))):
        response = client.get('/check_connection')
        response_json = response.get_json()
        assert response_json['success'] is True
        assert 'Błąd potwierdzeniem odpowiedzi serwera Allegro.' in response_json['error_message']
        assert response.status_code == 200

def test_data_display_too_many_requests(client, mocker):
    """Testuje obsługę błędu 429 Too Many Requests w data_display."""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.headers = {'Retry-After': '2'}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mocker.patch('requests.get', return_value=mock_response)
    response = client.post('/results', data={'phrase': 'test'})
    assert response.status_code == 302
    assert response.location == '/'

def test_data_display_server_error(client, mocker):
    """Testuje obsługę błędu 500+ w data_display."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=Mock(status_code=500))
    mocker.patch('requests.get', return_value=mock_response)
    response = client.post('/results', data={'phrase': 'test'})
    assert response.status_code == 200
    assert response.location is None

def test_data_display_timeout(client, mocker):
    """Testuje obsługę błędu Timeout w data_display."""
    mocker.patch('requests.get', side_effect=requests.exceptions.Timeout)
    response = client.post('/results', data={'phrase': 'test'})
    assert response.status_code == 302
    assert response.location == '/'

def test_data_display_unknown_error(client, mocker):
    """Testuje obsługę nieznanego błędu w data_display."""
    mocker.patch('requests.get', side_effect=Exception("Nieznany błąd"))
    response = client.post('/results', data={'phrase': 'test'})
    assert response.status_code == 302
    assert response.location == '/'
