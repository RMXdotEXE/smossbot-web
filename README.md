# smossbot
This GitHub repository contains all of the code for smossbot's website. It's important to know that this repository contains only the website for the code, and not for the bot itself (as I want to keep the bot's actual functionality private).

## Local testing
Because this code does not include the bot itself, several areas of the website that depend on the website making a direct connection to the bot, will not work. To get the website functional:
* install PostgreSQL 15 (or later, but 15 is the most up-to-date as of this writing) and configure it so that the website can communicate,
  * OR instead of installing PostgreSQL, change the database in Django to sqlite,
* create an API for the website to communicate with that listens on port 5000 (a barebones aiohttp server is sufficient, to allow the website to toggle active sessions for the user), and
* configure a .env file containing the variables outlined in the code (referred to in the code by os.getenv()).
