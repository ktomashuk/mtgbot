"""A module that consumes messages in"to-user" queue in RabbitMQ.
"""
import asyncio
import aio_pika
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.config import config
from bot.config.http_client import HttpClient
from bot.backend.commands import TelegramCommands
from bot.backend.backend import Backend

class FromUserListener:
  connection = None
  channel = None
  monitoring = True

  @classmethod
  async def connect(cls):
    """Creates a connection to RabbitMQ
    """
    retries = config.LISTENER_RECONNECT_RETRIES
    delay = config.LISTENER_RECONNECT_DELAY
    for attempt in range(retries):
      try:
        cls.connection = await aio_pika.connect_robust(
            **config.AIO_PIKA_PARAMETERS,
            heartbeat=60,
        )
        await cls.setup_queues()
        print("Connection to RabbitMQ established.")
        return cls.connection
      except (aio_pika.exceptions.AMQPConnectionError, OSError) as e:
        if attempt < retries - 1:
          text = (
              f"Connection attempt {attempt + 1} failed, "
              f"retrying in {delay} seconds..."
          )
          print(text)
          await asyncio.sleep(delay)
        else:
          print("Max retries reached, unable to connect to RabbitMQ.")
          raise e

  @classmethod
  async def monitor_connection(cls):
    """Checks if the connection is lost and attempts to reconnect.
    """
    while cls.monitoring:
      await asyncio.sleep(config.LISTENER_HEALTH_CHECK_DELAY)
      if cls.connection is None or cls.connection.is_closed:
        text = (
          f"Connection to {config.FROM_USER_QUEUE_NAME} lost! ",
          "Attempting to reconnect..."
        )
        print(text)
        await cls.connect()

  @classmethod
  async def setup_queues(cls):
    """Sets up the exchange and queues if they don't exist yet.
    """
    cls.channel = await cls.connection.channel()
    await cls.channel.declare_exchange(
        name=config.EXCHANGE_NAME,
        type=aio_pika.ExchangeType.DIRECT,
    )
    queue = await cls.channel.declare_queue(
        name=config.FROM_USER_QUEUE_NAME,
        durable=True,
    )
    await queue.bind(
        exchange=config.EXCHANGE_NAME,
        routing_key=config.FROM_USER_QUEUE_NAME,
    )
    await queue.consume(cls.callback, no_ack=False)

  @classmethod
  async def callback(cls, message: aio_pika.IncomingMessage):
    """Consumes the messages and resolves the corresponding backend commands.
    """
    async with message.process():
      async with cls.connection.channel() as channel:
        decoded_string = message.body.decode("utf-8")
        data_dict = json.loads(decoded_string)
        command = data_dict.get("command")
        chat_id = data_dict.get("chat_id")
        message_thread_id = data_dict.get("message_thread_id")
        message = data_dict.get("text")
        return_message = await TelegramCommands.resolve_command(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            command=command,
            message_text=message,
        )
        exchange = await channel.declare_exchange(
            name=config.EXCHANGE_NAME,
            type=aio_pika.ExchangeType.DIRECT,
        )
        if isinstance(return_message, list):
          for element in return_message:
            await exchange.publish(
              message=aio_pika.Message(body=element),
              routing_key=config.TO_USER_QUEUE_NAME,
            )
            if len(return_message) > 5:
              await asyncio.sleep(1)
        else:
          await exchange.publish(
              message=aio_pika.Message(body=return_message),
              routing_key=config.TO_USER_QUEUE_NAME,
          )

  @classmethod
  async def run_listener(cls):
    """Starts RabbitMQ listener.
    """
    await HttpClient.init_client()
    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        Backend.conflux_cache_scheduled_job,
        "cron",
        hour=3,
        minute=0,
        timezone="CET",
    )
    scheduler.add_job(
        Backend.deckboxes_cache_scheduled_job,
        "cron",
        hour=12,
        minute=0,
        timezone="CET",
    )
    scheduler.add_job(
        Backend.league_new_week_scheduled_job,
        "cron",
        day_of_week="mon",
        hour=10,
        minute=0,
        timezone="CET",
    )
    scheduler.start()

    connection = await cls.connect()
    monitor_connection = asyncio.create_task(cls.monitor_connection())
    try:
      await asyncio.Future()
      await connection.wait_closed()
    except KeyboardInterrupt:
      await connection.close()
    finally:
      monitor_connection.cancel()

if __name__ == "__main__":
  asyncio.run(FromUserListener.run_listener())
