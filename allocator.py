from threading import Thread

from config import Token
import telebot
from db_reqests import *
import os
import sys
import vk_api
import configparser
from time import sleep
import logging
import matplotlib.pyplot as plt

bot = telebot.TeleBot(Token)

config_path = os.path.join(sys.path[0], 'settings.ini')
config = configparser.ConfigParser()
config.read(config_path)
ACCESS_TOKEN_VK = config.get('VK', 'ACCESS_TOKEN_VK')
COUNT_MAIN = 1
PHOTO_PATH = 'Diagram.jpg'

message_breakers = [':', ' ', '\n']
labels = ["food", "taxes", "fun", "education", "utilities"]
max_message_length = 4091

logging.basicConfig(filename="inform.log", level=logging.INFO)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "/statistic 💯 Узнать, сколько Вы тратили в разных сферах\n"
                                      "/registration 🛂  Зарегистрироваться в систему (ФИ, наличность)\n"
                                      "/profile 👦 Профиль пользователя\n"
                                      "/income Указать прибыль ✅\n"
                                      "/expenses Указать убытки 📝\n"
                                      "/info VK - узнать свежую полезную информацию\n"
                                      "/help 🆘 Узнать описание команд\n"
                                      "/start 🔙 Повторить приветствие\n"
                                      "/vk_management Подписка, отписка от групп вк\n"
                                      "/my_groups Список подписок")


def create_main_markup():
    markup = telebot.types.ReplyKeyboardMarkup(True, True)
    button_statistic = telebot.types.KeyboardButton('💯')  # 💯 /statistic
    button_registration = telebot.types.KeyboardButton('🛂')  # 🛂 /registration
    button_profile = telebot.types.KeyboardButton('👦')  # 👦 /profile
    button_start = telebot.types.KeyboardButton('🔙')  # 🔙 /start
    button_income = telebot.types.KeyboardButton('✅')  # ✅ /income
    button_expenses = telebot.types.KeyboardButton('📝')  # 📝 /start
    button_vk_manage = telebot.types.KeyboardButton('+/-')  # 🔙 /add or delete vk groups
    button_groups = telebot.types.KeyboardButton('Группы')  # 🔙 /all user groups
    button_vk = telebot.types.KeyboardButton('VK')  # vk /info
    button_help = telebot.types.KeyboardButton('🆘')  # 🆘 /help
    markup.row(button_registration, button_income, button_expenses)
    markup.row(button_profile, button_statistic, button_help)
    markup.row(button_vk, button_vk_manage, button_groups)
    markup.row(button_start)
    return markup


# первое взаимодействие с ботом
@bot.message_handler(commands=['start'])
def start(message):
    markup = create_main_markup()
    bot.send_message(message.chat.id, 'Привет, это бот для ведения личных финансов!\n'
                                      'Здесь вы можете регулировать свои доходы и расходы!\n'
                                      'Используйте /help чтобы узнать команды', reply_markup=markup)

    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAJc8V-2w6lq33eMxp9tbsA2ZtBHpH8gAAJ0AAM7YCQUs8te1W3kR_QeBA')


def main_keyboard(message):
    markup = create_main_markup()
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAKJIF_eek6G_jdz5w8l_XqpXB85SQ74AAIeAAPANk8ToWBbLasAAd4EHgQ',
                     reply_markup=markup)


@bot.message_handler(commands=['income'])
def get_sum(message):
    next_message = bot.send_message(message.chat.id, 'Сколько нам добавить к Вашим наличным?')
    bot.register_next_step_handler(next_message, add_money)


def add_money(message):
    amount = message.text
    if not amount.isdigit():
        next_message = bot.send_message(message.chat.id, 'Вы ввели не число, пожалуйста, напишите число')
        bot.register_next_step_handler(next_message, add_money)
        return
    amount = int(amount)
    if amount < 0:
        next_message = bot.send_message(message.chat.id, 'Нельзя иметь отрицательный доход, пожалуйста, напишите '
                                                         'число не меньше 0')
        bot.register_next_step_handler(next_message, add_money)
        return
    is_existed, profile = get_profile(message.chat.id)
    if not is_existed:
        bot.send_message(message.chat.id, 'Эта функция доступна только зарегистрированным пользователям!'
                                          ' Пожалуйста, зарегистрируйтесь!')
        return
    new_amount = profile[0][1] + amount
    change_data_in_profile(message.chat.id, 'amount', new_amount)
    bot.send_message(message.chat.id, f'''Ваш счет успешно пополнен! Теперь у вас {new_amount}.''')


@bot.message_handler(commands=['expenses'])
def show_expenses(message):
    chat_id = message.chat.id
    exist, profile = get_profile(chat_id)
    if exist:
        markup = make_buttons()
        next_message = bot.send_message(message.chat.id,
                                        f"""Пожалуйста, выберите категорию Ваших трат.""",
                                        reply_markup=markup)
        bot.register_next_step_handler(next_message, choose_type)

    else:
        bot.send_message(message.chat.id, 'Эта функция доступна только зарегистрированным пользователям!'
                                          ' Пожалуйста, зарегистрируйтесь!')


data_type = ''


def choose_type(message):
    if message.text in ['food', 'taxes', 'fun', 'education', 'utilities']:
        next_message = bot.send_message(message.chat.id, 'Пожалуйста, введите Ваши траты!')
        global data_type
        data_type = message.text
        bot.register_next_step_handler(next_message, add_expenses)
        return
    if 'exit' in message.text:
        main_keyboard(message)
        return


def make_buttons():
    markup = telebot.types.ReplyKeyboardMarkup(True, True)
    button_food = telebot.types.KeyboardButton('food')
    button_taxes = telebot.types.KeyboardButton('taxes')
    button_fun = telebot.types.KeyboardButton('fun')
    button_education = telebot.types.KeyboardButton('education')
    button_utilities = telebot.types.KeyboardButton('utilities')
    button_exit = telebot.types.KeyboardButton('exit')
    markup.row(button_food, button_taxes, button_fun, button_education, button_utilities, button_exit)
    return markup


def add_expenses(message):
    global data_type
    if 'exit' in data_type:
        main_keyboard(message)
        return

    expense = message.text
    if not expense.isdigit():
        next_message = bot.send_message(message.chat.id, 'Вы ввели не число, пожалуйста, напишите число!')
        bot.register_next_step_handler(next_message, add_expenses)
        return
    expense = int(expense)
    chat_id = message.chat.id
    exist, profile = get_profile(chat_id)
    current_sum = profile[0][1]
    if current_sum < expense:
        next_message = bot.send_message(message.chat.id, 'Вы не можете потратить больше денег, чем имеете!')
        bot.register_next_step_handler(next_message, add_expenses)
        return

    change_data_in_profile(chat_id, 'amount', current_sum - expense)
    change_data_in_costs(chat_id, data_type, expense)

    markup = make_buttons()

    next_message = bot.send_message(message.chat.id, "Если Вы закончили указывать траты, нажмите exit.\nИначе, "
                                                     "выберите категорию.", reply_markup=markup)
    bot.register_next_step_handler(next_message, choose_type)


@bot.message_handler(commands=['statistic'])
def give_statistic(message):
    is_exist, expenses = get_all_expenses(message.chat.id)
    exist, profile = get_profile(message.chat.id)
    if not is_exist:
        bot.send_message(message.chat.id, 'Эта функция доступна только зарегистрированным пользователям!'
                                          ' Пожалуйста, зарегистрируйтесь!')
    else:
        expenses = expenses[0]
        fig, ax = plt.subplots()
        ax.pie(expenses, labels=labels, autopct='%1.1f%%', shadow=True,
               wedgeprops={'lw': 1, 'ls': '--', 'edgecolor': "k"}, rotatelabels=True)
        ax.axis("equal")
        plt.savefig(PHOTO_PATH)
        bot.send_message(message.chat.id, 'За последнее время Ваши траты были седующими')
        bot.send_photo(message.chat.id, open(PHOTO_PATH, 'rb'))
        bot.send_message(message.chat.id, f'''У вас осталось: {profile[0][1]}''')


@bot.message_handler(commands=['registration'])
def registration(message):
    is_existed, profile = get_profile(message.chat.id)
    if is_existed:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы\n Если вы хотите изменить данные зайдите в профиль")
        return

    next_message = bot.send_message(message.chat.id, """
    Введите пожалуйста на новых строчках 
    Имя
    Сумму, которой вы владеете
    """)
    bot.register_next_step_handler(next_message, registration_add_in_bd)


def exception_registration_add_in_bd(message):
    next_message = bot.send_message(message.chat.id, """
        Введите пожалуйста корректные данные
        Имя
        Сумму, которой вы владеете
        """)
    bot.register_next_step_handler(next_message, registration_add_in_bd)
    return


def registration_add_in_bd(message):
    list_name_room = message.text.split('\n')
    if len(list_name_room) != 2:
        exception_registration_add_in_bd(message)
        return

    name = list_name_room[0]  # неправильный ввод может быть
    if not list_name_room[1].isdigit():
        exception_registration_add_in_bd(message)
        return

    amount = int(list_name_room[1])
    chat_id = message.chat.id
    add_users(name=name, amount=amount, chat_id=chat_id)
    add_default_groups(message.chat.id)
    bot.send_message(message.chat.id, 'Пользователь успешно добавлен в систему')


def add_default_groups(chat_id):
    add_group(chat_id, 24864761, 'Бизнес-инкубатор ВШЭ')
    last_post_id = get_data(COUNT_MAIN, 24864761)['items'][0]['id']
    add_new_post(24864761, int(last_post_id))
    add_group(chat_id, 47706515, 'Стартап | Идеи для бизнеса, маркетинг')
    last_post_id = get_data(COUNT_MAIN, 47706515)['items'][0]['id']
    add_new_post(47706515, int(last_post_id))


@bot.message_handler(commands=['profile'])
def show_profile(message):
    chat_id = message.chat.id
    exist, profile = get_profile(chat_id)
    if exist:
        profile = profile[0]
        amount = profile[1]
        name = profile[0]

        markup = telebot.types.ReplyKeyboardMarkup(True, True)
        button_name = telebot.types.KeyboardButton('name')
        button_amount = telebot.types.KeyboardButton('amount')
        button_exit = telebot.types.KeyboardButton('exit')
        markup.row(button_name, button_amount, button_exit)

        next_message = bot.send_message(message.chat.id,
                                        f""" Name: {name}\nAmount: {amount}\n\nВы можете изменить данные""",
                                        reply_markup=markup)
        bot.register_next_step_handler(next_message, change_profile)

    else:
        bot.send_message(message.chat.id, 'Эта функция доступна только зарегистрированным пользователям!'
                                          ' Пожалуйста, зарегистрируйтесь!')


def change_profile(message):
    if message.text in ['name', 'amount']:
        next_message = bot.send_message(message.chat.id, 'Введите желаемые изменения')
        global data_type
        data_type = message.text
        bot.register_next_step_handler(next_message, change_data_in_profile_bot)
        return
    if 'exit' in message.text:
        main_keyboard(message)
        return


def change_data_in_profile_bot(message):
    global data_type
    if 'exit' in data_type:
        main_keyboard(message)
        return

    change_data_in_profile(message.chat.id, data_type, message.text)

    markup = telebot.types.ReplyKeyboardMarkup(True, True)
    button_name = telebot.types.KeyboardButton('name')
    button_amount = telebot.types.KeyboardButton('amount')
    button_exit = telebot.types.KeyboardButton('exit')
    markup.row(button_name, button_amount, button_exit)

    next_message = bot.send_message(message.chat.id, "Если вы закончили менять свой профиль, нажмите exit.\nИначе, "
                                                     "выберите то, что вы хотите изменить", reply_markup=markup)
    bot.register_next_step_handler(next_message, change_profile)


def start_vk_session():
    vk_session = vk_api.VkApi(token=ACCESS_TOKEN_VK)
    vk = vk_session.get_api()
    return vk


def get_data(count_vk, group_id):
    vk = start_vk_session()
    response = []
    try:
        response = vk.wall.get(owner_id='-' + str(group_id), count=count_vk)
    except vk_api.ApiError:
        logging.warning('Закрыттая группа')

    return response


def send_posts_vk_with_button(message_chat_id, group_id: int = None):
    posts = get_data(COUNT_MAIN, group_id=group_id)
    if posts:
        posts = posts['items']
        for post in posts:
            text = post['text']
            send_posts_text(text, message_chat_id)
            send_attachments(message_chat_id, post)
    else:
        bot.send_message(message_chat_id, 'Простите, но эта группа приватная, или закрытая. Мы не можем выдать '
                                          'Вам новую информацию по ней.')


def send_posts_vk_continuously():
    message_chat_ids = get_all_chat_ids()
    for chat_id in message_chat_ids:
        groups = get_persons_groups(chat_id)
        for group in groups:
            group_id = group[0]
            group_name = group[1]
            post = get_data(COUNT_MAIN, group_id=group_id)
            if post:
                post = post['items'][0]
                last_post_id = get_last_post_id(group_id)
                if not last_post_id:
                    logging.warning('User choose empty groop')
                elif int(post['id']) > last_post_id:
                    text = post['text']
                    send_posts_text(text, chat_id, group_name)
                    send_attachments(chat_id, post)
    groups = get_all_groups()
    for group in groups:
        group_id = group[0]
        post_id = group[1]
        post_id_last = get_data(COUNT_MAIN, group_id)
        if post_id_last:
            post_id_last = post_id_last['items'][0]['id']
            if post_id != int(post_id_last):
                update_last_post_id(group_id, post_id_last)


def send_posts_text(text, message_chat_id, group_name: str = None):
    if text != '':
        # Если слишком много символов, разделяем сообщение
        for message in split_text(text):
            try:
                if group_name:
                    bot.send_message(message_chat_id, f'Новая информация из группы {group_name}:')
                bot.send_message(message_chat_id, message, disable_web_page_preview=True)
            except telebot.apihelper.ApiException as e:
                logging.warning(e)
                break


def split_text(text):
    if len(text) >= max_message_length:
        last_index = max(
            map(lambda separator: text.rfind(separator, 0, max_message_length), message_breakers))
        good_part = text[:last_index]
        bad_part = text[last_index + 1:]
        return [good_part] + split_text(bad_part)
    else:
        return [text]


def send_attachments(message_chat_id, post):
    images = []
    if 'attachments' in post:
        attachment = post['attachments']
        for add in attachment:
            if add['type'] == 'photo':
                image = add['photo']
                images.append(image)
    if len(images) > 0:
        image_urls = list(map(lambda image: max(
            image["sizes"], key=lambda size: size["type"])["url"], images))
        try:
            bot.send_media_group(message_chat_id, list(map(
                lambda url: telebot.types.InputMediaPhoto(url), image_urls)))
        except telebot.apihelper.ApiException as e:
            logging.warning(e)


@bot.message_handler(commands=['vk_management'])
def get_operation(message):
    markup = telebot.types.ReplyKeyboardMarkup(True, True)
    button_add = telebot.types.KeyboardButton('add')
    button_delete = telebot.types.KeyboardButton('delete')
    button_exit = telebot.types.KeyboardButton('exit')
    markup.row(button_add, button_delete, button_exit)
    next_message = bot.send_message(message.chat.id, 'Что вы хотите сделать?\nДобавить группу:\nadd ID '
                                                     'группы/короткое название группы\n '
                                                     'Удалить группу:\ndelete ID группы/название группы\nexit - выход '
                                                     'на главную панель', reply_markup=markup)
    bot.register_next_step_handler(next_message, vk_setting)


def vk_setting(message):
    vk_operation = message.text
    if vk_operation == 'exit':
        main_keyboard(message)
        return
    is_existed_in_bd, profile = get_profile(message.chat.id)
    if not is_existed_in_bd:
        bot.send_message(message.chat.id,
                         'Чтобы иметь возможность подписываться на группы вк, пожалуйста зарегистрируйтесь!')
        return
    if vk_operation == 'add':
        next_message = bot.send_message(message.chat.id,
                                        'Пожалуйста, введите ID или короткое название группы, на которую хотите '
                                        'подписаться')
        bot.register_next_step_handler(next_message, vk_add)
        return
    if vk_operation == 'delete':
        next_message = bot.send_message(message.chat.id,
                                        'Пожалуйста, введите ID или название группы от которой хотите отписаться')
        bot.register_next_step_handler(next_message, vk_delete)
        return
    next_message = bot.send_message(message.chat.id,
                                    'Пожалуйста, нажмите на кнопку!')
    bot.register_next_step_handler(next_message, vk_setting)
    return


def vk_add(message):
    vk_id = message.text
    vk = start_vk_session()
    name_of_group = ''
    id_of_group = 0
    try:
        name_of_group = vk.groups.getById(group_id=vk_id)[0]['name']
        id_of_group = int(vk.groups.getById(group_id=vk_id)[0]['id'])
    except vk_api.ApiError:
        logging.warning('Wrong VK group name')
    if name_of_group == '':
        next_message = bot.send_message(message.chat.id,
                                        'Пожалуйста, введите правильный идентификатор группы!')
        bot.register_next_step_handler(next_message, vk_add)
        return
    is_existed, group_name = is_persons_group(message.chat.id, group_id=id_of_group)
    if is_existed:
        bot.send_message(message.chat.id,
                         f'Вы уже подписаны на группу {group_name}!')
        get_operation(message)
        return
    else:
        add_group(message.chat.id, id_of_group, name_of_group)
        is_already_existed = is_new_group(id_of_group)
        if is_already_existed:
            last_post_id = get_data(COUNT_MAIN, id_of_group)
            if last_post_id:
                last_post_id = last_post_id['items'][0]['id']
                add_new_post(id_of_group, int(last_post_id))
            else:
                bot.send_message(message.chat.id, 'Вы подписались на закрытую группу. Мы не сможем присылать Вам '
                                                  'новую информацию по ней')
        bot.send_message(message.chat.id, f'Вы успешно подписались на группу {name_of_group}')
        get_operation(message)
        return


def vk_delete(message):
    vk_operation = message.text
    if vk_operation.isdigit():
        is_existed, group_name = is_persons_group(message.chat.id, group_id=int(vk_operation))
        if not is_existed:
            bot.send_message(message.chat.id,
                             'К сожалению вы не подписаны на эту группу')
            get_operation(message)
            return
        else:
            delete_group(message.chat.id, group_id=vk_operation)
            bot.send_message(message.chat.id,
                             f'Вы успешно отписались от группы {group_name}')
            get_operation(message)
    else:
        is_existed, group_name = is_persons_group(message.chat.id, group_name=vk_operation)
        if not is_existed:
            bot.send_message(message.chat.id,
                             'К сожалению вы не подписаны на эту группу')
            get_operation(message)
            return
        else:
            delete_group(message.chat.id, group_name=group_name)
            bot.send_message(message.chat.id,
                             f'Вы успешно отписались от группы {group_name}')
            get_operation(message)


@bot.message_handler(commands=['my_groups'])
def persons_groups(message):
    """Функция для вывода пользователю списка всех групп, на которые он подписан"""
    list_of_groups = get_persons_groups(message.chat.id)
    text_of_message = ''
    for name_of_group in list_of_groups:
        text_of_message = text_of_message + name_of_group[1] + '\n'
    if text_of_message == '':
        bot.send_message(message.chat.id, 'К сожалению, вы не подписаны ни на что')
    else:
        bot.send_message(message.chat.id, text_of_message)


@bot.message_handler(commands=['info'])
def get_info(message):
    markup = telebot.types.InlineKeyboardMarkup()
    list_of_groups = get_persons_groups(message.chat.id)
    for group in list_of_groups:
        markup.add(telebot.types.InlineKeyboardButton(text=group[1], callback_data=str(group[0])))
    bot.send_message(message.chat.id, text='Выберите источник информации', reply_markup=markup)


# Inline keyboard
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    list_of_groups = get_persons_groups(call.message.chat.id)
    for group in list_of_groups:
        if call.data == str(group[0]):
            send_posts_vk_with_button(message_chat_id=call.message.chat.id, group_id=group[0])


def bot_telegram_polling():
    while True:
        try:
            global bot
            bot.polling(none_stop=True)
        except Exception as exception:
            logging.warning(exception)


def vk_post():
    while True:
        send_posts_vk_continuously()
        sleep(10)


@bot.message_handler(content_types=['text'])
def allocation_commands(message):
    if message.text == '💯':
        give_statistic(message)
    elif message.text == '✅':
        get_sum(message)
    elif message.text == '🛂':
        registration(message)
    elif message.text == '👦':
        show_profile(message)
    elif message.text == '📝':
        show_expenses(message)
    elif message.text == '🔙':
        start(message)
    elif message.text == 'VK':
        get_info(message)
    elif message.text == '🆘':
        help(message)
    elif message.text == '+/-':
        get_operation(message)
    elif message.text == 'Группы':
        persons_groups(message)


if __name__ == '__main__':
    Thread(target=bot_telegram_polling).start()
    Thread(target=vk_post).start()
