# -*- coding: utf-8 -*-
from telegram import ChatAction
from PIL import Image
import subprocess
import zipfile
import os
try:
    # For Python 3.0 and later
    from urllib.request import URLopener
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import URLopener

project_path = os.path.abspath('/home/pi/Projects/flai.xyz/assets/')
download_path = os.path.abspath(
    '/home/pi/Projects/telepybot/telepybot/.downloads')


def handle_update(bot, update, update_queue, **kwargs):
    chat_id = update.message.chat_id
    bot.sendMessage(chat_id=chat_id, text="Send blog file")

    while True:
        update = update_queue.get()
        bot.sendChatAction(chat_id, action=ChatAction.TYPING)
        if update.message.document:
            parse_blog(bot, chat_id, update)
            return
        elif update.message.text.lower() == "cancel":
            return
        elif update.message.text.startswith('/'):
            # User accesses another bot
            update_queue.put(update)
            break
        else:
            bot.sendMessage(chat_id=chat_id, text="Send blog file")


def parse_blog(bot, chat_id, update):
    file_id = update.message.document.file_id
    zippath, filename = download_file(update, bot.getFile(file_id))
    postpath = extract_post(zippath, filename)
    blogpath = os.path.dirname(postpath)

    bot.sendMessage(
        chat_id=chat_id, text="Converting images, this may take a while.")
    resize_images(postpath)

    construct_meta_post(postpath, filename, blogpath)
    convert_images_to_imagegroup(postpath)

    #pb.push_note('Blog updated', filename)
    #git.commit_push(project_path, '[blog update]')

    bot.sendMessage(chat_id=chat_id, text='Blog pushed')


def download_file(update, data):
    filename = update.message.document.file_name
    url = data.file_path
    file_path = os.path.join(download_path, filename)
    print(file_path)
    urlopener = URLopener()
    urlopener.retrieve(url, file_path)
    return file_path, filename.rsplit('.', 1)[0]


def extract_post(zippath, postname):
    blogpath = os.path.join(project_path, 'cycle', 'blog', 'posts')
    with zipfile.ZipFile(zippath, 'r') as zipped:
        zipped.extractall(os.path.join(blogpath, postname))
    return os.path.join(blogpath, postname)


def resize_images(path):
    # Need root priviledges
    #subprocess.call(["sudo", "modules/blog-image_resize.sh", path])
    subprocess.call(["modules/blog-image_resize.sh", path])


def construct_meta_post(path, filename, blogpath):
    # TODO: kato et jaakko on fiksannu nää
    # due to a bug the app, need to rename the posts.txt to post.txt
    os.rename(os.path.join(path, 'posts.txt'), os.path.join(path, 'post.txt'))

    print(os.path.join(path, 'post.txt'))
    with open(os.path.join(path, 'post.txt'), 'r') as post:
        text = post.read()
        title, trip, date_range, main_image = \
            [x.split(' ', 1)[1] for x in text.split('\n')[0:4]]
        main_image = main_image[:-1]
        meta = '|'.join([filename, trip, title, date_range, main_image])

    with open(os.path.join(os.path.dirname(blogpath), 'posts.txt'),
              'a') as posts:
        posts.write('\n' + meta)


def convert_images_to_imagegroup(path):
    with open(os.path.join(path, 'post.txt'), 'r') as post:
        lines = post.read().split('\n')

    fixed_lines = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("main-image:"):
            lines[i] = lines[i][:-1]
        image_group = []
        prev_line = lines[i]
        while lines[i].startswith('image: '):
            line, caption = lines[i].split("|")
            if caption != "":
                # if image has caption, it can't be in image group
                break
            tag, content = line.split(': ', 1)
            width, height = Image.open(os.path.join(path, 'orig',
                                                    content)).size
            image_group.append('{}?{}x{}'.format(content, width, height))
            i += 1
        if len(image_group) > 1:
            fixed_lines.append('image-group: ' + ' '.join(image_group))
        elif len(image_group) == 1:
            fixed_lines.append(prev_line)
        fixed_lines.append(lines[i])
        i += 1

    with open(os.path.join(path, 'post.txt'), 'w') as post:
        post.write('\n'.join(fixed_lines))
