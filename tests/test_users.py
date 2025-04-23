import requests
import pytest
import time
from .conftest import BASE_URL, OTHER_USER_ID

# Пропускаем все тесты в этом файле, если ID другого пользователя не задан
pytestmark = pytest.mark.skipif(not OTHER_USER_ID, reason="Не задана переменная окружения MATTERMOST_OTHER_USER_ID для тестов управления пользователями")

def _ensure_user_not_in_channel(headers, channel_id, user_id):
    """Вспомогательная функция: удаляет пользователя из канала, если он там есть."""
    delete_user_url = f"{BASE_URL}/api/v4/channels/{channel_id}/members/{user_id}"
    print(f"Проверка/удаление пользователя {user_id} из канала {channel_id} перед тестом.")
    response = requests.delete(delete_user_url, headers=headers, timeout=10)
    if response.status_code == 200:
        print(f"Пользователь {user_id} удален из канала {channel_id}.")
    elif response.status_code == 404 or (response.status_code == 403 and "manage_channel_members" in response.text):
        # 404 - его там и не было, 403 - нет прав ИЛИ его там не было (зависит от версии)
         print(f"Пользователь {user_id} не найден в канале {channel_id} или нет прав на удаление (статус {response.status_code}).")
    else:
        print(f"Предупреждение: Не удалось проверить/удалить пользователя {user_id} из канала {channel_id} перед тестом. Статус: {response.status_code}")
    time.sleep(1) # Небольшая пауза после удаления

def _ensure_user_in_channel(headers, channel_id, user_id):
    """Вспомогательная функция: добавляет пользователя в канал, если его там нет."""
    add_user_url = f"{BASE_URL}/api/v4/channels/{channel_id}/members"
    payload = {"user_id": user_id}
    print(f"Проверка/добавление пользователя {user_id} в канал {channel_id} перед тестом.")
    response = requests.post(add_user_url, headers=headers, json=payload, timeout=10)
    if response.status_code == 201:
        print(f"Пользователь {user_id} добавлен в канал {channel_id}.")
    elif response.status_code == 400 and "already a member" in response.text.lower():
        print(f"Пользователь {user_id} уже был в канале {channel_id}.")
    elif response.status_code == 403:
         pytest.fail(f"Ошибка прав доступа: не удалось добавить пользователя {user_id} в канал {channel_id}. Проверьте права основного пользователя.", pytrace=False)
    else:
        # Пробуем получить список участников, чтобы убедиться, что он там
        get_members_url = f"{BASE_URL}/api/v4/channels/{channel_id}/members"
        get_resp = requests.get(get_members_url, headers=headers, timeout=10)
        if get_resp.status_code == 200:
             members = get_resp.json()
             if any(member['user_id'] == user_id for member in members):
                 print(f"Пользователь {user_id} уже был в канале {channel_id} (проверено через список).")
                 return # Все ок, он там
        # Если не удалось добавить и не удалось подтвердить наличие - ошибка
        pytest.fail(f"Не удалось добавить пользователя {user_id} в канал {channel_id}. Статус: {response.status_code}, Ответ: {response.text[:200]}", pytrace=False)
    time.sleep(1) # Небольшая пауза после добавления


def test_add_user_to_channel_success(headers, test_channel):
    """
    Сценарий: Проверка добавления пользователя в чат/канал.
    Шаги:
        1. Получить ID канала из фикстуры test_channel.
        2. Убедиться, что пользователя OTHER_USER_ID нет в канале (удалить, если есть).
        3. Отправить POST запрос на /channels/{channel_id}/members с user_id=OTHER_USER_ID.
        4. (Опционально) Проверить список участников канала.
    Ожидаемый результат: Статус-код 201 Created, пользователь добавлен в канал.
    """
    channel_id = test_channel['id']
    user_to_add = OTHER_USER_ID

    # 2. Убедиться, что пользователя нет
    _ensure_user_not_in_channel(headers, channel_id, user_to_add)

    # 3. Добавляем пользователя
    add_user_url = f"{BASE_URL}/api/v4/channels/{channel_id}/members"
    payload = {"user_id": user_to_add}
    print(f"\nТест: Добавление пользователя {user_to_add} в канал {channel_id}")
    response = requests.post(add_user_url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    assert response.status_code == 201, f"Ожидался статус 201 при добавлении пользователя, получен {response.status_code}. Ответ: {response.text[:200]}"

    member_data = response.json()
    assert member_data.get("user_id") == user_to_add, "ID добавленного пользователя не совпадает"
    assert member_data.get("channel_id") == channel_id, "ID канала в ответе не совпадает"
    print(f"Пользователь {user_to_add} успешно добавлен в канал {channel_id}.")

    # 4. Проверка списка участников (опционально, но полезно)
    get_members_url = f"{BASE_URL}/api/v4/channels/{channel_id}/members"
    get_response = requests.get(get_members_url, headers=headers, timeout=10)
    assert get_response.status_code == 200, "Не удалось получить список участников для проверки"
    members = get_response.json()
    assert any(member['user_id'] == user_to_add for member in members), f"Пользователь {user_to_add} не найден в списке участников после добавления"
    print(f"Пользователь {user_to_add} подтвержден в списке участников канала {channel_id}.")


def test_remove_user_from_channel_success(headers, test_channel):
    """
    Сценарий: Проверка удаления пользователя из чата/канала.
    Шаги:
        1. Получить ID канала из фикстуры test_channel.
        2. Убедиться, что пользователь OTHER_USER_ID есть в канале (добавить, если нет).
        3. Отправить DELETE запрос на /channels/{channel_id}/members/{user_id} с user_id=OTHER_USER_ID.
        4. (Опционально) Проверить список участников канала.
    Ожидаемый результат: Статус-код 200 OK, пользователь удален из канала.
    """
    channel_id = test_channel['id']
    user_to_remove = OTHER_USER_ID

    # 2. Убедиться, что пользователь есть в канале
    _ensure_user_in_channel(headers, channel_id, user_to_remove)

    # 3. Удаляем пользователя
    delete_user_url = f"{BASE_URL}/api/v4/channels/{channel_id}/members/{user_to_remove}"
    print(f"\nТест: Удаление пользователя {user_to_remove} из канала {channel_id}")
    response = requests.delete(delete_user_url, headers=headers, timeout=10)
    response.raise_for_status()
    assert response.status_code == 200, f"Ожидался статус 200 при удалении пользователя, получен {response.status_code}. Ответ: {response.text[:200]}"

    result = response.json()
    # Ответ может быть {"status": "ok"} или просто {}
    assert result is not None, "Ответ при удалении пользователя не должен быть пустым (если ожидается JSON)"
    print(f"Пользователь {user_to_remove} успешно удален из канала {channel_id}.")

    # 4. Проверка списка участников (опционально)
    get_members_url = f"{BASE_URL}/api/v4/channels/{channel_id}/members"
    get_response = requests.get(get_members_url, headers=headers, timeout=10)
    assert get_response.status_code == 200, "Не удалось получить список участников для проверки после удаления"
    members = get_response.json()
    assert not any(member['user_id'] == user_to_remove for member in members), f"Пользователь {user_to_remove} все еще найден в списке участников после удаления"
    print(f"Пользователь {user_to_remove} не найден в списке участников канала {channel_id} (как и ожидалось).")