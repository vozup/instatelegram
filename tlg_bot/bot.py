import os
from pathlib import Path
import filetype

import telebot
from telebot import types
from common.config import Config
from common.common import get_site_name, get_file_size, get_dir_size, make_dirs
from loader.main_loader import Loader

# TODO Add limit of file for users

token = Config().get_telegram_token()
bot = telebot.TeleBot(token)
L = Loader()
TELEGRAM_TIMEOUT = Config().get_telegram_config()['timeout']


def start_bot(username=None, password=None,
              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:111.0) Gecko/20100101 Firefox/111.0"):
    """
    Start pooling bot with login on instagram or not
    Login need only on Linux system
    WARNING: if you login instagram can mark you like a spam or block your account
    :param username: instagram username
    :param password: instagram password
    :return:
    """
    try:
        # Login to instagram
        global L
        home_dir = str(Path.home())
        L.instance.context.user_agent = user_agent
        print(f"Using agent: {user_agent}")
        if username:
            path_to_session = Path(home_dir, 'instaloader', "session-" + username)
            if os.path.exists(path_to_session):
                L.instance.load_session_from_file(username, path_to_session)
            elif password:
                L.instance.login(username, password)
                L.instance.save_session_to_file(path_to_session)
            else:
                print(f"Can't find previous session file {path_to_session}")
                print(f"Try starting bot without authentication to instagram")
        bot.polling(none_stop=True, interval=0)
    except telebot.apihelper.ApiTelegramException:
        print(f"Bot don't started. Change {Path('instaloader.conf').absolute()} file. Add your telegram token.")


def home_markup():
    """
    Markup for Home command
    :return: markup
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Show available files")
    btn2 = types.KeyboardButton('Status')
    btn3 = types.KeyboardButton('Button 2')
    markup.add(btn1, btn2, btn3)

    return markup


def markup_for_file(media_files: list):
    """
    Markup for "Show available files" command
    Create KeyboardButton according to the files in the user's folder
    :param media_files: media file lists from user dir
    :return: created markup
    """

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for media_filename in media_files:
        btn = types.KeyboardButton(media_filename)
        markup.add(btn)

    back_btn = types.KeyboardButton('Home')
    delete_all = types.KeyboardButton("Delete all files")
    markup.add(back_btn, delete_all)

    return markup


def markup_for_status():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Downloaded files")
    btn2 = types.KeyboardButton('Subscription')
    btn3 = types.KeyboardButton('Home')
    markup.add(btn1, btn2, btn3)

    return markup


@bot.message_handler(commands=['start'])
def start(message):
    make_dirs(Path(L.base_download_path, message.from_user.username))
    bot.send_message(message.from_user.id, "Hello!", reply_markup=home_markup())


@bot.message_handler(content_types=['text'], regexp='.*\\.(gif|jpe?g|bmp|png|mp4|avi)$')
def handle_message(message):
    """
    Handling push on button with media file names
    :param message:
    :return:
    """
    full_file_path = Path(L.base_download_path, message.from_user.username, message.text)
    chat_id = message.from_user.id
    # TODO Simplify
    keyboard = [[types.InlineKeyboardButton('Delete', callback_data='delete:' + str(full_file_path))]]
    reply_markup = types.InlineKeyboardMarkup(keyboard)
    kind = filetype.guess(full_file_path)

    try:
        with open(full_file_path, 'rb') as media:
            bot.send_message(chat_id, "Wait a while")
            if kind.mime.startswith('image'):
                bot.send_photo(chat_id, media, reply_markup=reply_markup, timeout=TELEGRAM_TIMEOUT)
            if kind.mime.startswith('video'):
                bot.send_video(chat_id, media, reply_markup=reply_markup, timeout=TELEGRAM_TIMEOUT)
    except FileNotFoundError as err:
        bot.send_message(chat_id, err.strerror)


@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    chat_id = call.message.chat.id
    username = call.from_user.username
    file_list = os.listdir(Path(L.base_download_path + username))
    # Delete media file
    if call.data.startswith('delete'):
        file_witch_del = call.data.lstrip('delete:')
        file_name = Path(file_witch_del).name
        try:
            os.remove(Path(file_witch_del))
            file_list.remove(file_name)
        except FileNotFoundError:
            print("File not found")
        finally:
            bot.send_message(chat_id, 'Deleted', reply_markup=markup_for_file(file_list))


def delete_all_files(dir_name):
    try:
        files_in_dir = os.listdir(Path(dir_name))
        for file_name in files_in_dir:
            os.remove(Path(dir_name, file_name))
        return True
    except FileNotFoundError:
        print("File not found for deleting")
        return False


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_directory = Path(L.base_download_path, message.from_user.username)
    # Handling http links
    if message.text.startswith('http'):
        full_site_name, sht_site_name = get_site_name(message.text)
        # Handling instagram http link
        if sht_site_name == 'instagram':
            post = L.get_post(message.text)
            post_type = post.typename
            author = post.owner_username
            shortcode = post.shortcode
            # Download post from IG to server
            res = L.download_post(message.text, dir_name=message.from_user.username)
            if res is None:
                # If connection error
                return
            if res:
                bot.send_message(message.from_user.id, f"{post_type} by {author} downloaded!")
            bot.send_message(message.from_user.id, f"Wait a while")
            # Upload downloaded post from server to chat back
            send_media_file(message.from_user, post_type, shortcode)
        # Handling tiktok http link
        elif sht_site_name == 'tiktok':
            bot.send_message(message.from_user.id, f"I still do not know how to download files from {full_site_name}")
        # Unknown http link
        else:
            bot.send_message(message.from_user.id, f"Unknown site {full_site_name}")
    # Show to user all files which downloaded to server
    elif message.text == "Show available files":
        file_list = []
        try:
            file_list = os.listdir(user_directory)
            file_sizes = '{:.3f}'.format(get_dir_size(user_directory))
            bot.send_message(message.from_user.id, f"All file size {file_sizes} Mb")
        except FileNotFoundError:
            print(f"Try to have access to non-existent directory {user_directory}")
        if len(file_list) > 0:
            bot.send_message(message.from_user.id, 'Downloaded files',
                             reply_markup=markup_for_file(file_list))
        else:
            bot.send_message(message.from_user.id, "You don't have downloaded files")
    elif message.text == "Delete all files":
        if delete_all_files(user_directory):
            bot.send_message(message.from_user.id, "All file deleted", reply_markup=home_markup())
        else:
            bot.send_message(message.from_user.id, "We have some error when deleting files")
    # Status button
    elif message.text == "Status":
        bot.send_message(message.from_user.id, 'Status info', reply_markup=markup_for_status())
    elif message.text == "Downloaded files":
        file_sizes = '{:.3f}'.format(get_dir_size(user_directory))
        bot.send_message(message.from_user.id, f"You use {file_sizes} Mb",
                         reply_markup=markup_for_status())
    elif message.text == "Subscription":
        bot.send_message(message.from_user.id, "Your subscription is FREE, and you have 100Mb per folder on server",
                         reply_markup=markup_for_status())
    # Show home markup
    elif message.text == 'Home':
        bot.send_message(message.from_user.id, 'Home', reply_markup=home_markup())
    # Unknown text command
    else:
        bot.send_message(message.from_user.id, "Unknown command")


def is_size_allowed(file_path, for_photo=10, for_video=50):
    """
    Check file size is allowed by telegram
    :param file_path: full file path
    :param for_photo: allowed size for photo in Mb
    :param for_video: allowed size for video in Mb
    :return:
    """
    try:
        file_size = get_file_size(file_path, 'mb')
        kind = filetype.guess(file_path)
        print(f"{kind.mime} Size in MegaBytes is %.3f" % file_size)
        if kind.mime.startswith('image') and file_size < for_photo:
            return True
        elif kind.mime.startswith('video') and file_size < for_video:
            return True
        else:
            return False
    except FileNotFoundError:
        print("File not found")


def send_media_file(message_from_user, media_type: str, shortcode: str, media_group_size=10):
    """
    Determination of the type of uploaded post
    :param media_type: GraphVideo GraphImage GraphSidecar
    :param message_from_user:
    :param shortcode: shortcode of post to search for a file name
    :param media_group_size: count of media in one telegram media_group
    :return:
    """
    file_path = Path(L.base_download_path, message_from_user.username, shortcode)
    # TODO Try to simplify GraphVideo and GraphImage
    if media_type == "GraphVideo":
        file_path = Path(str(file_path) + '.mp4')
        if is_size_allowed(file_path):
            try:
                with open(file_path, 'rb') as video:
                    bot.send_video(message_from_user.id, video, timeout=TELEGRAM_TIMEOUT)
            except FileNotFoundError:
                bot.send_message(message_from_user.id, "Wrong video file or file path")
        else:
            bot.send_message(message_from_user.id, "Video file to large")
    elif media_type == "GraphImage":
        file_path = Path(str(file_path) + '.jpg')
        if is_size_allowed(file_path):
            try:
                with open(file_path, 'rb') as image:
                    bot.send_photo(message_from_user.id, image, timeout=TELEGRAM_TIMEOUT)
            except FileNotFoundError:
                bot.send_message(message_from_user.id, "Wrong photo file or file path")
        else:
            bot.send_message(message_from_user.id, "Photo file to large")
    # If link on album
    elif media_type == "GraphSidecar":
        files = os.listdir(Path(L.base_download_path + message_from_user.username))
        album = list()
        opened_files = {}

        try:
            # Create dict with IO opened files dict(IO Stream: mime type)
            for file_name in files:
                full_file_path = Path(L.base_download_path, message_from_user.username, file_name)
                if file_name.startswith(shortcode) and is_size_allowed(full_file_path):
                    media = open(full_file_path, 'rb')
                    mime = filetype.guess(full_file_path).mime
                    opened_files[media] = mime
            # Creating list with InputMediaFiles
            count = 0
            for media, mime in opened_files.items():
                if mime.startswith('image'):
                    album.append(types.InputMediaPhoto(media))
                elif mime.startswith('video'):
                    album.append(types.InputMediaVideo(media))
                # If we have big list (bigger then media_group_size)
                # Send first part of media group with count media_group_size
                if count + 1 == media_group_size:
                    bot.send_media_group(message_from_user.id, album, timeout=TELEGRAM_TIMEOUT)
                    album.clear()
                # Send rest of files or all if we have end of files
                if len(opened_files) == count + 1:
                    bot.send_media_group(message_from_user.id, album, timeout=TELEGRAM_TIMEOUT)

                count += 1
        except FileNotFoundError:
            print("Wrong media file or file path")
        finally:
            # Close opened IO stream files
            for media in opened_files.keys():
                media.close()
