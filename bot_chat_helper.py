import random

import openai
import telebot

from config import GPT_TOKEN, TELEGRAM_TOKEN, TELEGRAM_ADMIN

openai.api_key = GPT_TOKEN
bot = telebot.TeleBot(TELEGRAM_TOKEN)

users = {}
file_name_config = 'config_chat_id'


class User:
    def __init__(self, _id):
        self.id = str(_id)
        self.message = ''
        self.publish = {}
        self.message_for_deleting = []

    pass


def get_user(_id) -> User:
    if users.get(_id) is None:
        users.update({_id: User(_id)})

    return users.get(_id)


def get_chat_id():
    with open(file_name_config, 'r') as f:
        chat_id = f.read()
    return chat_id.strip()


class Command:
    set_chat = 'set_chat'
    summary = 'summary'
    publish = 'publish'


@bot.message_handler(content_types=["text"])
def get_text(message):
    user = get_user(message.from_user.id)
    if user.id not in TELEGRAM_ADMIN:
        bot.send_message(message.from_user.id, 'You are not Admin')
        for admin in TELEGRAM_ADMIN:
            bot.send_message(admin, f'Unknown user: {message.from_user}, You can add as Admin')
        return

    user.message = message.text

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(text='Give me summery, 30 words', callback_data=f"{Command.summary}|30"))
    keyboard.add(telebot.types.InlineKeyboardButton(text='Give me summery, 50 words', callback_data=f"{Command.summary}|50"))
    keyboard.add(telebot.types.InlineKeyboardButton(text='Give me summery, 100 words', callback_data=f"{Command.summary}|100"))

    bot.send_message(message.from_user.id, 'Select command', reply_markup=keyboard)


@bot.channel_post_handler(content_types=["text"])
def get_channel_text(message):
    if str(message.chat.id) != get_chat_id():
        for admin in TELEGRAM_ADMIN:
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(
                telebot.types.InlineKeyboardButton(
                    text='Setup the chat for publishing', callback_data=f"{Command.set_chat}|{message.chat.id}")
            )
            bot.send_message(admin, f'New chat: "{message.chat.title}", '
                                    f'If you want to publish here, Click Setup button', reply_markup=keyboard)


@bot.callback_query_handler(lambda query: query.data.startswith(Command.set_chat))
def callback_set_chat(query):
    user = get_user(query.from_user.id)
    chat_id = query.data.split("|")[-1]
    with open(file_name_config, 'w') as f:
        f.write(chat_id)
    bot.send_message(user.id, 'Ok')


@bot.callback_query_handler(lambda query: query.data.startswith(Command.summary))
def callback_summary(query):
    user = get_user(query.from_user.id)
    count = query.data.split("|")[-1]

    for url in user.message.split():
        message = f"This is link {url}, Give me summary of this article. Should be {count} words."

        bot.send_message(user.id, f">>> {message} <<<\n==============================================")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}]
        )

        result = ''
        for choice in response.choices:
            result += choice.message.content

        keyboard = telebot.types.InlineKeyboardMarkup()
        num = random.randint(1, 1000)
        keyboard.add(telebot.types.InlineKeyboardButton(text='Publish it', callback_data=f"{Command.publish}|{num}"))

        user.publish.update({num: f"{url}{result}"})
        bot.send_message(user.id, f"{url}{result}", reply_markup=keyboard)


@bot.callback_query_handler(lambda query: query.data.startswith(Command.publish))
def callback_publish(query):
    user = get_user(query.from_user.id)
    num = int(query.data.split("|")[-1])
    if user.publish.get(num):
        bot.send_message(get_chat_id(), user.publish.pop(num))
        bot.send_message(user.id, "Ok")
    else:
        bot.send_message(user.id, "Error")


if __name__ == "__main__":
    bot.polling(none_stop=True)
