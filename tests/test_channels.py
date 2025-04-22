import requests
import pytest
import uuid
from .conftest import BASE_URL, TEAM_ID

def test_create_channel_success(headers, test_channel):
    """
    Сценарий: Проверка успешного создания нового канала.
    Шаги: Фикстура test_channel создает канал.
    Ожидаемый результат: Фикстура отрабатывает без ошибок, данные канала корректны.
                       Фикстура также удаляет канал после теста.
    """
    assert test_channel is not None, "Данные канала не должны быть None"
    assert "id" in test_channel, "ID канала отсутствует в ответе"
    assert "name" in test_channel and "test-auto-" in test_channel["name"], "Имя канала некорректно"
    assert test_channel.get("team_id") == TEAM_ID, "ID команды в созданном канале не совпадает"
    print(f"Тест успешного создания канала (ID: {test_channel['id']}) пройден.")


def test_create_channel_duplicate_name(headers):
    """
    Сценарий: Проверка обработки ошибок при создании канала с уже существующим именем.
    Шаги:
        1. Создать канал с уникальным именем.
        2. Попытаться создать второй канал с тем же именем в той же команде.
        3. Удалить первый созданный канал (cleanup).
    Ожидаемый результат: Вторая попытка создания возвращает статус-код 400 Bad Request или 500 с ошибкой о дубликате.
    """
    channel_name = f"duplicate-test-{uuid.uuid4().hex[:8]}"
    create_url = f"{BASE_URL}/api/v4/channels"
    payload = {
        "team_id": TEAM_ID,
        "name": channel_name,
        "display_name": f"Канал для теста дубликатов {channel_name}",
        "type": "O"
    }
    created_channel_id = None

    try:
        # 1. Первое создание
        print(f"\nТест дубликата: Создание первого канала {channel_name}")
        response1 = requests.post(create_url, headers=headers, json=payload, timeout=10)
        response1.raise_for_status() # Убедимся, что первый создался
        assert response1.status_code == 201, f"Первое создание канала не удалось: {response1.status_code}, {response1.text[:200]}"
        created_channel_id = response1.json()['id']
        print(f"Первый канал {channel_name} (ID: {created_channel_id}) создан.")

        # 2. Второе создание с тем же именем
        print(f"Тест дубликата: Попытка создания второго канала с именем {channel_name}")
        response2 = requests.post(create_url, headers=headers, json=payload, timeout=10)
        # Ожидаем ошибку клиента (400) или иногда сервер может вернуть 500 при такой ошибке
        assert response2.status_code in [400, 500], f"Ожидался статус 400 или 500 при создании дубликата, получен {response2.status_code}. Ответ: {response2.text[:200]}"
        # Проверяем текст ошибки (может меняться в разных версиях Mattermost)
        error_text = response2.text.lower()
        assert "store.sql_channel.save_channel.exists.app_error" in error_text or \
               "channel with that name already exists" in error_text or \
               "канал с таким названием уже существует" in error_text, \
               f"В ответе об ошибке не найдено ожидаемое сообщение о дубликате имени: {response2.text[:200]}"
        print(f"Получен ожидаемый статус {response2.status_code} при попытке создать дубликат канала.")

    finally:
        # 3. Удаление первого созданного канала
        if created_channel_id:
            delete_url = f"{BASE_URL}/api/v4/channels/{created_channel_id}"
            print(f"Тест дубликата: Удаление канала {created_channel_id}")
            del_response = requests.delete(delete_url, headers=headers, timeout=10)
            if del_response.status_code == 200:
                 print(f"Канал {created_channel_id} успешно удален.")
            else:
                 print(f"Предупреждение: Не удалось удалить канал {created_channel_id} после теста дубликата. Статус: {del_response.status_code}")