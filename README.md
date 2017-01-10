# telepybot

telepybot is a modular Telegram bot written in Python. It is built using
[python-telegram-bot][1], which is a python wrapper for Telegram Bot API.
telepybot contains several modules, for example weather forecast searcher
and cycle route searcher. I'm running telepybot on a Raspberry Pi, which is a
tiny low powered computer. The main motivation for building this bot was to find
a easy and fast way to update [my brothers cycle blog][2].

Overview of few modules:
* **blog**: Updates [flai.xyz][2] cycle blog.
* **echo**: A small sample module to demonstrate how modules can be added.
* **elevation**: Searches a route between locations using [Google Maps Directions API][3],
and finds rough altitude points along that route using [Google Maps Elevation API][4].
Elevation graph is drawn using [matplotlib][5].
* **gps-analyzer**: Updates [flai.xyz][6] gps routes and calculates few statistics
for user.
* **wol**: Starts up a predefined computer on network using wake on lan.

## How to use this bot
1. Download the repository: `git clone https://github.com/anttilip/telepybot.git`
2. Navigate to telepybot folder and install dependencies:
`pip install -r requirements.txt`
    * **Note**: some dependencies can be relieved if you don't use my sample modules.
3. Add your Telegram bot token to `telepybot.conf` file.
4. Run the bot: `python telepybot.py`
    * This bot is tested with python 2.7 and 3.5

## Adding new modules
To add new modules, place the module file to `modules` folder (along with all
current modules) and add new line to modules.json file. modules.json uses syntax:
`"keyword": "myModule.py"`.

Now that everything should be set up, you can trigger your new module by sending
message `/keyword` to your bot. This keyword is what you have defined in modules.json.


### Module structure
Modules must have a function called `handle_update`, which is called when user
triggers the module by calling `/keyword`. In simplest form module could look
like this:
```python
def handle_update(bot, update):
    # Users unique chat id
    chat_id = update.message.chat_id
    # Message that user sent, e.g. /keyword wohoo!
    message_user_sent = update.message.text

    # Send something back to user
    bot.sendMessage(chat_id=chat_id, text='Nice message!')

```

This bot relies heavily on [python-telegram-bot][1]. Luckily their documentation
is great so you will find some great tips from there.


[1]: https://github.com/python-telegram-bot/python-telegram-bot "python-telegram-bot"
[2]: http://flai.xyz/blog "flai.xyz/blog"
[3]: https://developers.google.com/maps/documentation/directions/
[4]: https://developers.google.com/maps/documentation/elevation/
[5]: http://matplotlib.org/
[6]: http://flai.xyz/tours "flai.xyz/tours"

