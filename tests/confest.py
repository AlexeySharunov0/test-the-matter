import pytest
import requests
import os
import uuid
import time
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение конфигурации из переменных окружения
BASE_URL = os.getenv("MATTERMOST_BASE_URL")
LOGIN_ID = os.getenv("MATTERMOST_USER_LOGIN")
PASSWORD = os.getenv("MATTERMOST_USER_PASSWORD")
TEAM_ID = os.getenv("MATTERMOST_TEST_TEAM_ID")
OTHER_USER_ID = os.getenv("MATTERMOST_OTHER_USER_ID")
LOCKED_USER_LOGIN = os.getenv("MATTERMOST_LOCKED_USER_LOGIN")
LOCKED_USER_PASSWORD = os.getenv("MATTERMOST_LOCKED_USER_PASSWORD")
INACTIVE_USER_LOGIN = os.getenv("MATTERMOST_INACTIVE_USER_LOGIN")
INACTIVE_USER_PASSWORD = os.getenv("MATTERMOST_INACTIVE_USER_PASSWORD")

# Проверка наличия обязательных переменных
if not all([BASE_URL, LOGIN_ID, PASSWORD, TEAM_ID]):
    pytest.exit("ОШИБКА: Не установлены обязательные переменные окружения: MATTERMOST_BASE_URL, MATTERMOST_USER_LOGIN, MATTERMOST_USER_PASSWORD, MATTERMOST_TEST_TEAM_ID", returncode=1)


@pytest.fixture(scope="session")
def auth_token():
    """
    Фикстура для получения токена аутентификации один раз за сессию.
    Проверяет успешный логин основного тестового пользователя.
    """
    login_url = f"{BASE_URL}/api/v4/users/login"
    payload = {"login_id": LOGIN_ID, "password": PASSWORD}
    headers = {"Content-Type": "application/json"}
    try:
        print(f"\nAttempting login for user: {LOGIN_ID} at {BASE_URL}")
        response = requests.post(login_url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()  # Вызовет исключение для кодов 4xx/5xx
        token = response.headers.get("Token")
        if not token:
             pytest.fail(f"Не удалось получить токен. Статус: {response.status_code}, Ответ: {response.text[:500]}...", pytrace=False)
        print("Успешная аутентификация, токен получен.")
        return token
    except requests.exceptions.Timeout:
         pytest.fail(f"Таймаут при попытке логина к {login_url}", pytrace=False)
    except requests.exceptions.ConnectionError:
        pytest.fail(f"Ошибка соединения с {login_url}. Убедитесь, что Mattermost доступен.", pytrace=False)
    except requests.exceptions.HTTPError as e:
        pytest.fail(f"HTTP ошибка при логине: {e}. Статус: {e.response.status_code}, Ответ: {e.response.text[:500]}...", pytrace=False)
    except Exception as e:
        pytest.fail(f"Неожиданная ошибка при аутентификации: {e}", pytrace=False)

@pytest.fixture(scope="function")
def headers(auth_token):
    """Фикстура для создания стандартных заголовков с токеном авторизации."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope="function")
def test_channel(headers):
    """
    Фикстура для создания временного тестового канала перед тестом
    и его удаления после теста (cleanup).
    """
    channel_data = None # Инициализация на случай ошибки создания
    channel_name = f"test-auto-{uuid.uuid4().hex[:8]}"
    create_url = f"{BASE_URL}/api/v4/channels"
    payload = {
        "team_id": TEAM_ID,
        "name": channel_name,
        "display_name": f"Временный тестовый канал {channel_name}",
        "type": "O"  # Публичный канал
    }
    try:
        print(f"\nСоздание тестового канала: {channel_name}")
        response = requests.post(create_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status() # Проверка на ошибки создания
        channel_data = response.json()
        channel_id = channel_data['id']
        print(f"Тестовый канал создан: ID={channel_id}, Name={channel_name}")

        yield channel_data  # Передаем данные канала в тест

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Не удалось создать тестовый канал: {e}", pytrace=False)
    finally:
        # Очистка: удаление канала после выполнения теста
        if channel_data and 'id' in channel_data:
            channel_id = channel_data['id']
            delete_url = f"{BASE_URL}/api/v4/channels/{channel_id}"
            try:
                print(f"\nУдаление тестового канала: {channel_id}")
                del_response = requests.delete(delete_url, headers=headers, timeout=10)
                if del_response.status_code == 200:
                    print(f"Тестовый канал {channel_id} успешно удален.")
                elif del_response.status_code == 404:
                     print(f"Тестовый канал {channel_id} уже был удален или не найден.")
                else:
                    print(f"Предупреждение: Не удалось удалить тестовый канал {channel_id}. Статус: {del_response.status_code}, Ответ: {del_response.text[:200]}")
            except requests.exceptions.RequestException as e:
                print(f"Предупреждение: Ошибка при удалении тестового канала {channel_id}: {e}")