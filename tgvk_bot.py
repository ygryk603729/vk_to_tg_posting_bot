import os
import time
import vk_api
import telethon
import pygetwindow as gw
from telethon import TelegramClient
from getpass import getpass
import requests
import asyncio
import re
import sys
from telethon.tl.types import InputFile

D = 2 # - за сколько дней выполнять проверку?

# VK API
VK_GROUP_ID = '186471220'  # ID твоего сообщества # 186471220 - Радиус # 229790854 - моя тест группа
VK_ACCESS_TOKEN = 'vk1.a.F2xp9MbrseeqLSPuJqSX0pNjUiQKFcgS9TI15oiwYr5ccEQ3AzPPK6H0Fj2PolaPrjN4K1XerFB6wmBXk9pX0VVbgyIiNC3RGy3t-GjHjG5QfT6BF45oNHSPPvtiuv98_xNxa2nyAEdi7QCP-0PvvgwgzVigmqowHa6BVpihAFWQGEvgRJKxsvRl2g85xRS8BtI8oZsNYW3mh-tn3aQylA'


# Telegram API
TELEGRAM_API_ID = '22646857'
TELEGRAM_API_HASH = '91c49d10054720b9f29f319746124c70'
TELEGRAM_BOT_TOKEN = '7633938147:AAHLO5AwGjx80ltPyNLVsFZXixW28BOWAmU'
TELEGRAM_CHANNEL = '@VSK_RadiusTeam'  # Юзернейм канала или ID #@VSK_RadiusTeam #@bot_tg_test_1

# Подключение к VK API
vk_session = vk_api.VkApi(token=VK_ACCESS_TOKEN)
vk = vk_session.get_api()

# Подключение к Telegram
client = TelegramClient('bot_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)


def get_latest_vk_posts():
    """Получает последние посты из VK за 12 часов"""
    response = vk.wall.get(owner_id=-int(VK_GROUP_ID), count=5)

    posts = []
    
    for post in response['items']:
        post_time = post['date']
        if time.time() - post_time <= 86400*D:  # 24 часов в секундах
            posts.append(post)
    
    return posts


def is_telegram_open():
    """Проверяет, открыт ли Telegram"""
    windows = gw.getWindowsWithTitle('Telegram')
    return len(windows) > 0


def open_telegram():
    """Запускает Telegram, если он закрыт"""
    if not is_telegram_open():
        os.startfile("C:\\Users\\ikane\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe")  # Укажи путь, если нужно
        time.sleep(5)  # Ждём, пока Telegram загрузится




async def send_post_to_telegram(post):
    """Отправляет пост в Telegram с прикреплёнными изображениями"""
    message = clean_vk_links(post['text'])
    photos = []

    # Проверяем, есть ли изображения
    if 'attachments' in post:
        for i, att in enumerate(post['attachments']):
            if att['type'] == 'photo':
                largest_photo = max(att['photo']['sizes'], key=lambda x: x['height'])
                photo_url = largest_photo['url']

                # Скачиваем картинку
                try:
                    response = requests.get(photo_url)
                    response.raise_for_status()
                    filename = f"temp_photo_{i}.jpg"  # Уникальное имя
                    with open(filename, "wb") as file:
                        file.write(response.content)
                    photos.append(filename)
                except Exception as e:
                    print(f"Ошибка при загрузке изображения: {e}")

    # Подключаем клиент, если он не запущен
    if not client.is_connected():
        await client.connect()

    # Отправляем сообщение и все фото одним сообщением
    if photos:
        await client.send_file(TELEGRAM_CHANNEL, photos, caption=message)
    else:
        await client.send_message(TELEGRAM_CHANNEL, message)

    # Удаляем временные файлы
    for photo in photos:
        if os.path.exists(photo):
            os.remove(photo)
            
def clean_vk_links(text):
    """Заменяет VK-ссылки вида [https://vk.com/xxx|"Название"] на https://vk.com/xxx - Название.
    Также обрабатывает ссылки вида [club215249537|Название] и преобразует их в https://vk.com/club215249537 - Название"""
    
    # Обработка стандартных ссылок
    text = re.sub(r'\[(https://[^|]+)\|(.*?)\]', r'\1 - \2', text)
    
    # Обработка ссылок вида [club215249537|Название]
    text = re.sub(r'\[club(\d+)\|(.*?)\]', r'https://vk.com/club\1 - \2', text)
    
    return text

def add_to_autostart():
    """Добавляет бота в автозапуск Windows"""
    script_path = os.path.abspath(sys.argv[0])
    bat_path = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup', 'bot_autorun.bat')
    with open(bat_path, 'w') as bat_file:
        bat_file.write(f'start /min python "{script_path}"')

async def main():
    posts = get_latest_vk_posts()
    if not posts:
        print("Новых постов нет")
        return
    
    for post in posts:
        print("Найден новый пост:")
        print(post['text'])
        user_input = input("Продублировать в Telegram? (y/n): ")
        
        if user_input.lower() == 'y':
            open_telegram()
            await send_post_to_telegram(post)  # !!! Теперь с await
            print("Пост отправлен!")
        else:
            print("Пропущен.")

if __name__ == '__main__':
    #add_to_autostart() #пока не работает - при перезапуске бот запускается но по всей видимости не обнаруживает постов и мгновенно закрывается
    asyncio.run(main())  # Запускаем корректно