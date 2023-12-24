"""Configuration variables for other modules.
"""
from dotenv import load_dotenv
import os
import requests

load_dotenv()

# RabbitMQ variables
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME")
FROM_USER_QUEUE_NAME = os.getenv("FROM_USER_QUEUE_NAME")
TO_USER_QUEUE_NAME = os.getenv("TO_USER_QUEUE_NAME")

# Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Discrod bot token
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# AIO Pika
AIO_PIKA_PARAMETERS = {
    "url": f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/",
}

# Listeners connection details
LISTENER_RECONNECT_RETRIES = 20
LISTENER_RECONNECT_DELAY = 5
LISTENER_HEALTH_CHECK_DELAY = 120

# MongoDB
MONGO_CONNECTION = os.getenv("MONGO_CONNECTION")

# Deckbox
DECKBOX_LOGIN = os.getenv("DECKBOX_LOGIN")
DECKBOX_PASSWORD = os.getenv("DECKBOX_PASSWORD")
DECKBOX_COOKIE = ""
DECKBOX_COOKIE_LAST_LOGIN = ""