import random

import openai
import telebot

from config import GPT_TOKEN, TELEGRAM_TOKEN, TELEGRAM_ADMIN

openai.api_key = GPT_TOKEN

bot = telebot.TeleBot(TELEGRAM_TOKEN)
users = {}


class User:
    def __init__(self, _id):
        self.id = str(_id)
        self.message = ''
        self.publish = {}

    pass


def get_user(_id) -> User:
    if users.get(_id) is None:
        users.update({_id: User(_id)})

    return users.get(_id)


def get_chat_id():
    with open('config_chat_id', 'r') as f:
        chat_id = f.read()
    return chat_id.strip()


@bot.channel_post_handler(content_types=["text"])
def get_channel_text(message):
    if str(message.chat.id) != get_chat_id():
        for admin in TELEGRAM_ADMIN:
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(
                telebot.types.InlineKeyboardButton(
                    text='Setup the chat for publishing', callback_data=f"set_chat|{message.chat.id}")
            )
            bot.send_message(admin, f'New chat: "{message.chat.title}", '
                                    f'If you want to publish here, Click Setup button', reply_markup=keyboard)


@bot.message_handler(content_types=["text"])
def get_text(message):
    print(message.from_user.id)

    user = get_user(message.from_user.id)
    # if user.id not in TELEGRAM_ADMIN:
    #     bot.send_message(message.from_user.id, 'You are not Admin')
    #     return

    user.message = message.text

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(text='Give me summery, 30 words', callback_data=f"summery|30"))
    keyboard.add(telebot.types.InlineKeyboardButton(text='Give me summery, 50 words', callback_data=f"summery|50"))
    keyboard.add(telebot.types.InlineKeyboardButton(text='Give me summery, 100 words', callback_data=f"summery|100"))

    bot.send_message(message.from_user.id, 'Select command', reply_markup=keyboard)


@bot.callback_query_handler(lambda query: query.data.startswith('set_chat'))
def callback_set_chat(query):
    user = get_user(query.from_user.id)
    chat_id = query.data.split("|")[-1]
    with open('config_chat_id', 'w') as f:
        f.write(chat_id)
    bot.send_message(user.id, 'Ok')


@bot.callback_query_handler(lambda query: query.data.startswith('summery'))
def callback_summery(query):
    user = get_user(query.from_user.id)
    count = query.data.split("|")[-1]
    message = f"This is link {user.message}, Give me summary of this article. Should be {count} words."

    bot.send_message(user.id, f">>{message}...")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "user", "content": message},
            ]
    )

    result = ''
    for choice in response.choices:
        result += choice.message.content

    keyboard = telebot.types.InlineKeyboardMarkup()
    num = random.randint(1, 1000)
    keyboard.add(telebot.types.InlineKeyboardButton(text='Publish it', callback_data=f"publish|{num}"))

    user.publish.update({num: f"{user.message}{result}"})
    bot.send_message(user.id, f"{user.message}{result}", reply_markup=keyboard)


@bot.callback_query_handler(lambda query: query.data.startswith('publish'))
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