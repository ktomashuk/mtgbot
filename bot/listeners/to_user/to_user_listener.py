import asyncio
import aio_pika
import json
from bot.config import config
from bot.telegram.bot import MagicBot
from bot.config.http_client import HttpClient

class ToUserListener:
  connection = None
  channel = None
  monitoring = True

  @classmethod
  async def connect(cls):
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
    while cls.monitoring:
      await asyncio.sleep(config.LISTENER_HEALTH_CHECK_DELAY)
      if cls.connection is None or cls.connection.is_closed:
        text = (
          f"Connection to {config.TO_USER_QUEUE_NAME} lost! ",
          "Attempting to reconnect..."
        )
        print(text)
        await cls.connect()

  @classmethod
  async def setup_queues(cls):
    cls.channel = await cls.connection.channel()
    await cls.channel.declare_exchange(
        name=config.EXCHANGE_NAME,
        type=aio_pika.ExchangeType.DIRECT,
    )
    queue = await cls.channel.declare_queue(
        name=config.TO_USER_QUEUE_NAME,
        durable=True,
    )
    await queue.bind(
        exchange=config.EXCHANGE_NAME,
        routing_key=config.TO_USER_QUEUE_NAME,
    )
    await queue.consume(cls.callback, no_ack=False)

  @classmethod
  async def callback(cls, message: aio_pika.IncomingMessage):
    async with message.process():
      print(f"Received {message.body} in the {config.TO_USER_QUEUE_NAME} queue")
      decoded_string = message.body.decode("utf-8")
      data_dict = json.loads(decoded_string)
      command = data_dict.get("command")
      chat_id = data_dict.get("chat_id")
      message = data_dict.get("text")
      status = data_dict.get("status")
      options = data_dict.get("options", {})
      if not options:
        options = {}
      match command:
        case "text":
          if isinstance(options, dict):
            disable_preview = options.get("disable_preview", True)
          await MagicBot.send_message_to_user(
              chat_id=chat_id,
              message=message,
              disable_preview=disable_preview,
          )
        case "image":
          await MagicBot.send_image_to_user(chat_id=chat_id, image_url=message)
        case "menu":
          disable_preview = True
          if isinstance(options, dict):
            disable_preview = options.get("disable_preview", True)
          await MagicBot.send_menu_to_user(
              chat_id=chat_id,
              message=message,
              registered=status,
              disable_preview=disable_preview,
          )
        case "poll":
          await MagicBot.send_poll_to_channel(
              chat_id=chat_id,
              message=message,
              answers=options,
          )
        case "quiz":
          if isinstance(options, dict):
            card_name = options.get("card_name", "")
            art = options.get("art", "")
          await MagicBot.send_quiz_image_to_chat(
              chat_id=chat_id,
              card_name=card_name,
              image_url=art,
          )
        case "void":
          pass

  @classmethod
  async def run_listener(cls):
    await HttpClient.init_client()
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
  asyncio.run(ToUserListener.run_listener())
