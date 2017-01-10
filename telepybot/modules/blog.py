"""*Handles flai.xyz blog updates.*

This module is designed to update flai.xyz cycling blog. Update is sent as
a .zip or splitted file, e.g. .zip.1o3. Update is processed and pushed to
[blogs assets repo](https://github.com/JaakkoLipsanen/assets/).

Usage:
```
  /blog
  > Send .zip file
```
"""

from telegram import ChatAction
import subprocess
import zipfile
import os
try:
    # For Python 3.0 and later
    from urllib.request import URLopener
    from configparser import ConfigParser
except ImportError:
    # Fall back to Python 2's urllib2 and ConfigParser
    from urllib import URLopener
    from ConfigParser import ConfigParser

config = ConfigParser()
config.read('telepybot.conf')
project_path = config.get('blog', 'projectPath')
download_path = config.get('blog', 'downloadPath')


def handle_update(bot, update, update_queue, **kwargs):
    chat_id = update.message.chat_id
    bot.sendMessage(chat_id=chat_id, text="Send blog file")

    zip_path, post_name = get_zip(bot, chat_id, update_queue)
    if zip is None:
        bot.sendMessage(chat_id=chat_id, text="No files received, aborting")

    parse_blog(bot, chat_id, zip_path, post_name)


def get_zip(bot, chat_id, update_queue):
    zip_parts = None
    while True:
        update = update_queue.get()
        document = update.message.document
        bot.sendChatAction(chat_id, action=ChatAction.TYPING)

        if document is not None:
            file = download_file(update, bot.getFile(document.file_id))
            if is_full_zip(document):
                # file name is in format name.zip
                post_name = document.file_name.rsplit('.', 1)[0]
                return file, post_name

            if zip_parts is None:
                zip_parts = [None] * get_zip_part_count(document)

            zip_index = get_zip_part_index(document)
            zip_parts[zip_index] = file

            if None in zip_parts:
                bot.sendMessage(chat_id=chat_id, text='Send another split')
            else:
                # file name is in format name.zip.3o3
                post_name = document.file_name.rsplit('.', 2)[0]
                return combine_zip(zip_parts), post_name

        elif update.message.text.lower() == "cancel":
            return None

        elif update.message.text.startswith('/'):
            # User accesses another bot
            update_queue.put(update)
            return None

        else:
            bot.sendMessage(chat_id=chat_id, text="Send blog file")


def is_full_zip(document):
    # Check if file name ends with '.zip'
    return document.file_name.rsplit('.', 1)[-1] == 'zip'


def get_zip_part_count(document):
    # file is in format name.zip.1o3, so convert last char to int
    return int(document.file_name[-1])


def get_zip_part_index(document):
    # file is in format name.zip.1o3, so convert
    # third last char to int and start indexing from 0
    return int(document.file_name[-3]) - 1


def combine_zip(splits):
    merged_path = os.path.join(download_path, 'merged.zip')
    with open(merged_path, 'wb') as merged:
        for file in splits:
            with open(file, 'rb') as split:
                merged.write(split.read())

    return merged_path


def parse_blog(bot, chat_id, zip_path, post_name):
    post_path = extract_post(zip_path, post_name)
    blog_path = os.path.dirname(post_path)

    bot.sendMessage(
        chat_id=chat_id, text="Converting images, this may take a while.")
    resize_images(post_path)

    construct_meta_post(post_path, post_name, blog_path)
    convert_images_to_imagegroup(post_path)

    #pb.push_note('Blog updated', filename)
    commit_and_push(post_name)
    #git.commit_push(project_path, '[blog update]')

    bot.sendMessage(chat_id=chat_id, text='Blog pushed')


def download_file(update, data):
    filename = update.message.document.file_name
    url = data.file_path
    file_path = os.path.join(download_path, filename)

    urlopener = URLopener()
    urlopener.retrieve(url, file_path)

    return file_path


def extract_post(zippath, postname):
    blogpath = os.path.join(project_path, 'cycle', 'blog', 'posts')
    with zipfile.ZipFile(zippath, 'r') as zipped:
        zipped.extractall(os.path.join(blogpath, postname))
    return os.path.join(blogpath, postname)


def resize_images(path):
    subprocess.call(["sh", "modules/blog-image-resize.sh", path])


def construct_meta_post(path, filename, blogpath):
    with open(os.path.join(path, 'post.txt'), 'r') as post:
        text = post.read()
        title, trip, date_range, main_image = \
            [x.split(' ', 1)[1] for x in text.split('\n')[0:4]]
        main_image = main_image.rsplit('?', 1)[0]
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
            _, content = line.split(': ', 1)
            image_group.append(content)
            i += 1
        if len(image_group) > 1:
            fixed_lines.append('image-group: ' + ' '.join(image_group))
        elif len(image_group) == 1:
            fixed_lines.append(prev_line)
        fixed_lines.append(lines[i])
        i += 1

    with open(os.path.join(path, 'post.txt'), 'w') as post:
        post.write('\n'.join(fixed_lines))


def commit_and_push(post_name):
    current_dir = os.getcwd()
    os.chdir(project_path)
    subprocess.call(['git', 'pull'])
    subprocess.call(['git', 'add', '.'])
    message = '[blog update] ({})'.format(post_name)
    subprocess.call(['git', 'commit', '-m', message])
    subprocess.call(['git', 'push'])
    os.chdir(current_dir)
