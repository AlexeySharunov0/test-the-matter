import requests
import pytest
import time
import uuid
from .conftest import BASE_URL

def test_send_message_success(headers, test_channel):
    """
    Сценарий: Проверка отправки сообщения в чат/канал.
    Шаги:
        1. Получить ID канала из фикстуры test_channel.
        2. Отправить POST запрос на /posts с ID канала и текстом сообщения.
    Ожидаемый результат: Статус-код 201 Created, в ответе есть отправленное сообщение.
    """
    channel_id = test_channel['id']
    post_url = f"{BASE_URL}/api/v4/posts"
    message_text = f"Автотестовое сообщение {uuid.uuid4().hex[:8]} в канал {channel_id}"
    payload = {
        "channel_id": channel_id,
        "message": message_text
    }
    print(f"\nТест: Отправка сообщения в канал {channel_id}")
    response = requests.post(post_url, headers=headers, json=payload, timeout=10)
    response.raise_for_status() # Проверка на HTTP ошибки
    assert response.status_code == 201, f"Ожидался статус 201 при отправке сообщения, получен {response.status_code}. Ответ: {response.text[:200]}"

    post_data = response.json()
    assert "id" in post_data, "ID сообщения отсутствует в ответе"
    assert post_data.get("message") == message_text, "Текст отправленного сообщения не совпадает"
    assert post_data.get("channel_id") == channel_id, "ID канала в отправленном сообщении не совпадает"
    print(f"Сообщение (ID: {post_data['id']}) успешно отправлено.")


def test_receive_messages_success(headers, test_channel):
    """
    Сценарий: Проверка получения сообщений из чат/канала.
    Шаги:
        1. Получить ID канала из фикстуры test_channel.
        2. Отправить тестовое сообщение в этот канал.
        3. Подождать немного.
        4. Отправить GET запрос на /channels/{channel_id}/posts.
    Ожидаемый результат: Статус-код 200 OK, в ответе содержится список постов, включая отправленное сообщение.
    """
    channel_id = test_channel['id']
    post_url = f"{BASE_URL}/api/v4/posts"
    get_posts_url = f"{BASE_URL}/api/v4/channels/{channel_id}/posts"

    # 2. Отправляем сообщение
    message_text = f"Сообщение для проверки получения {uuid.uuid4().hex[:8]}"
    payload = {"channel_id": channel_id, "message": message_text}
    print(f"\nТест: Отправка сообщения для проверки получения в канал {channel_id}")
    send_response = requests.post(post_url, headers=headers, json=payload, timeout=10)
    send_response.raise_for_status()
    assert send_response.status_code == 201, "Не удалось отправить сообщение для теста получения"
    sent_post_id = send_response.json()['id']
    print(f"Сообщение для получения (ID: {sent_post_id}) отправлено.")

    # 3. Ждем немного, чтобы сообщение точно обработалось сервером
    time.sleep(2)

    # 4. Получаем сообщения
    print(f"Тест: Получение сообщений из канала {channel_id}")
    response = requests.get(get_posts_url, headers=headers, timeout=10)
    response.raise_for_status()
    assert response.status_code == 200, f"Ожидался статус 200 при получении сообщений, получен {response.status_code}. Ответ: {response.text[:200]}"

    posts_data = response.json()
    assert "posts" in posts_data, "Ключ 'posts' отсутствует в ответе при получении сообщений"
    assert "order" in posts_data, "Ключ 'order' отсутствует в ответе при получении сообщений"

    # Ищем наше отправленное сообщение в словаре posts
    received_post = posts_data.get("posts", {}).get(sent_post_id)
    assert received_post is not None, f"Отправленное сообщение (ID: {sent_post_id}) не найдено в списке полученных"
    assert received_post.get("message") == message_text, "Текст полученного сообщения не совпадает с отправленным"
    print(f"Отправленное сообщение (ID: {sent_post_id}) успешно найдено в канале.")