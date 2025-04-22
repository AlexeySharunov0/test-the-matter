import requests
import pytest
from .conftest import BASE_URL, LOGIN_ID, PASSWORD, LOCKED_USER_LOGIN, LOCKED_USER_PASSWORD, INACTIVE_USER_LOGIN, INACTIVE_USER_PASSWORD

def test_successful_authentication(auth_token):
    """
    Сценарий: Проверка успешной аутентификации пользователя с использованием корректных учетных данных.
    Шаги: Фикстура auth_token выполняет логин.
    Ожидаемый результат: Фикстура отрабатывает без ошибок, auth_token не None.
    """
    assert auth_token is not None, "Токен не должен быть None при успешной аутентификации"

def test_authentication_invalid_credentials():
    """
    Сценарий: Проверка обработки ошибок при аутентификации с некорректными учетными данными.
    Шаги:
        1. Отправить POST запрос на /users/login с неверным логином/паролем.
    Ожидаемый результат: Статус-код 401 Unauthorized.
    """
    login_url = f"{BASE_URL}/api/v4/users/login"
    payload = {"login_id": f"invalid_user_{uuid.uuid4().hex[:6]}", "password": "invalid_password"}
    headers = {"Content-Type": "application/json"}
    print(f"\nТест: Попытка логина с неверными данными: {payload['login_id']}")
    response = requests.post(login_url, json=payload, headers=headers, timeout=10)
    assert response.status_code == 401, f"Ожидался статус 401, получен {response.status_code}. Ответ: {response.text[:200]}"
    print("Получен ожидаемый статус 401 для неверных учетных данных.")

# --- Тесты, требующие предварительной настройки ---

@pytest.mark.skipif(not LOCKED_USER_LOGIN or not LOCKED_USER_PASSWORD, reason="Не заданы переменные окружения для заблокированного пользователя (MATTERMOST_LOCKED_USER_LOGIN/PASSWORD)")
def test_authentication_locked_account():
    """
    Сценарий: Попытаться войти в заблокированную учетную запись.
    Предусловия: Существует заблокированный пользователь с данными из .env.
    Шаги:
        1. Отправить POST запрос на /users/login с учетными данными заблокированного пользователя.
    Ожидаемый результат: Статус-код 401 Unauthorized или 403 Forbidden с сообщением о блокировке.
    """
    login_url = f"{BASE_URL}/api/v4/users/login"
    payload = {"login_id": LOCKED_USER_LOGIN, "password": LOCKED_USER_PASSWORD}
    headers = {"Content-Type": "application/json"}
    print(f"\nТест: Попытка логина заблокированным пользователем: {LOCKED_USER_LOGIN}")
    response = requests.post(login_url, json=payload, headers=headers, timeout=10)
    # Mattermost обычно возвращает 401 для заблокированных аккаунтов, но может зависеть от конфигурации
    assert response.status_code == 401, f"Ожидался статус 401 для заблокированного аккаунта, получен {response.status_code}. Ответ: {response.text[:200]}"
    # Можно добавить проверку текста ошибки, если он стабилен
    # assert "account is blocked" in response.json().get("message", "").lower(), "В ответе нет сообщения о блокировке"
    print(f"Получен ожидаемый статус {response.status_code} для заблокированного пользователя.")


def test_authentication_server_connection_simulation():
    """
    Сценарий: Симулировать отсутствие соединения с сервером аутентификации.
    Шаги:
        1. Попытаться отправить запрос на несуществующий порт или IP.
    Ожидаемый результат: Исключение requests.exceptions.ConnectionError или TimeoutError.
    """
    # Используем заведомо неверный URL/порт
    invalid_url = "http://localhost:9999/api/v4/users/login"
    payload = {"login_id": "any_user", "password": "any_password"}
    headers = {"Content-Type": "application/json"}
    print(f"\nТест: Попытка соединения с недоступным сервером: {invalid_url}")
    with pytest.raises((requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        # Используем маленький таймаут для ускорения теста
        requests.post(invalid_url, json=payload, headers=headers, timeout=1)
    print("Получено ожидаемое исключение ConnectionError/Timeout при попытке соединения с недоступным сервером.")


@pytest.mark.skipif(not INACTIVE_USER_LOGIN or not INACTIVE_USER_PASSWORD, reason="Не заданы переменные окружения для неактивного пользователя (MATTERMOST_INACTIVE_USER_LOGIN/PASSWORD)")
def test_authentication_inactive_account():
    """
    Сценарий: Попытаться войти с учетной записью, которая не была активирована.
    Предусловия: Существует неактивированный пользователь с данными из .env.
    Шаги:
        1. Отправить POST запрос на /users/login с учетными данными неактивного пользователя.
    Ожидаемый результат: Статус-код 401 Unauthorized или 403 Forbidden с сообщением о неактивности.
    """
    login_url = f"{BASE_URL}/api/v4/users/login"
    payload = {"login_id": INACTIVE_USER_LOGIN, "password": INACTIVE_USER_PASSWORD}
    headers = {"Content-Type": "application/json"}
    print(f"\nТест: Попытка логина неактивным пользователем: {INACTIVE_USER_LOGIN}")
    response = requests.post(login_url, json=payload, headers=headers, timeout=10)
    assert response.status_code == 401, f"Ожидался статус 401 для неактивного аккаунта, получен {response.status_code}. Ответ: {response.text[:200]}"
    # Можно добавить проверку текста ошибки, если он стабилен
    # assert "account is not active" in response.json().get("message", "").lower(), "В ответе нет сообщения о неактивности"
    print(f"Получен ожидаемый статус {response.status_code} для неактивного пользователя.")