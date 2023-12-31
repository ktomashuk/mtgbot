"""Module for running the telegram bot.
"""
import json
import time
from datetime import datetime
from aio_pika import (connect_robust, ExchangeType, Message)
from telegram import (Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)
from telegram import ReplyKeyboardRemove
from bot.config import config
from bot.utils.utils import Utils
from bot.mongo.mongo_client import MongoClient

class MagicBot:
  bot = Bot(token=config.BOT_TOKEN)
  input = 0

  @classmethod
  async def start_with_keyboard(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Handles any message received by a bot.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    user = update.message.from_user
    username = user.username
    await cls.send_message_to_queue(
        command="start",
        chat_id=update.effective_chat.id,
        message_text=username,
    )

  @classmethod
  async def send_message_to_user(
      cls,
      chat_id: str,
      message: str,
      disable_preview: bool = True,
  ) -> None:
    """Sends a message to a user.

    Args:
      chat_id: id of the chat with the user
      message: message that will be sent to the user
    """
    await cls.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="HTML",
        disable_web_page_preview=disable_preview,
    )

  @classmethod
  async def forward_message_to_chat(
      cls,
      from_chat_id: str,
      to_chat_id: str,
      message_id: str,
  ) -> None:
    """Forwards a message from chat to chat.

    Args:
      from_chat_id: id of the chat the message is forwarded from
      to_chat_id: id of the chat the message is forwarded to
      message_id: ID of the forwarded message 
    """
    await cls.bot.forward_message(
        chat_id=to_chat_id,
        from_chat_id=from_chat_id,
        message_id=message_id,
    )

  @classmethod
  async def send_menu_to_user(
      cls,
      chat_id: str,
      message: str,
      registered: bool,
      disable_preview: bool = True,
  ) -> None:
    """Sends a menu to a user.

    Args:
      chat_id: id of the chat with the user
      message: message that will be sent to the user
      registered: check if the user is registere,
      disable_preview: check if the url previews should be disabled
    """
    keyboard = [["/reg",]]
    if registered:
      keyboard = [
          ["/search", "/wish"],
          ["/dbsub", "/dbunsub"],
          ["/regdeckbox", "/updatedeckbox"],
          ["/mydeckbox", "/mydeckboxsubs"],
          ["/help", "/edhdanas"],
      ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )
    if len(message) > 3900:
      message = "Please be more specific."
    await cls.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="HTML",
        reply_markup=reply_markup,
        disable_web_page_preview=disable_preview,
    )

  @classmethod
  async def send_poll_to_channel(
      cls,
      chat_id: str,
      message: str,
      answers: list[str],
  ) -> bool:
    """Sends a poll to the channel.

    Args:
      chat_id: id of the chat with the user
      message: message in the poll
      answers: a list of answers
    Returns:
      A bool showing if poll result was added to mongo
    """
    poll_message = await cls.bot.send_poll(
        chat_id=chat_id,
        question=message,
        options=answers,
        is_anonymous=False,
    )
    message_id = poll_message.message_id
    now = datetime.now()
    datetime_string = now.strftime("%Y-%m-%d")
    edh_danas_object = {
      "chat_id": chat_id,
      "message_id": message_id,
      "timestamp": datetime_string,
    }
    result = await MongoClient.add_edh_danas(object=edh_danas_object)
    return result

  @classmethod
  async def start_bulk_subsribe(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> int:
    """Handles opening the input for subscribing to deckboxes.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    result_text = (
      "Please enter the list of deckboxes to subsribe to.\n"
      "Each deckbox must be on a separate line.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.input

  @classmethod
  async def start_bulk_card_search(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> int:
    """Handles opening the input for searching cards.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    result_text = (
      "Please enter the list of cards to look for.\n"
      "Each card must be on a separate line.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.input

  @classmethod
  async def start_bulk_unsubsribe(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> int:
    """Handles opening the input for unsubscribing from deckboxes.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    result_text = (
      "Please enter the list of deckboxes to unsubsribe from.\n"
      "Each deckbox must be on a separate line.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.input

  @classmethod
  async def start_deckbox_register(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> int:
    """Handles opening the input for registering a deckboxe.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    result_text = (
      "Please enter your deckbox name.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.input

  @classmethod
  async def handle_bulk_subscribe(
      cls,
      update: Update,
      context: CallbackContext
  ) -> ConversationHandler.END:
    """Processes the input for subscribing to deckboxes.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      A conversation handler that stops the conversation with the user
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      user_input = update.message.text
      lines = user_input.split("\n")
      for line in lines:
        message_object = {
            "telegram": username,
            "deckbox": line,
        }
        message_string = json.dumps(message_object)
        await cls.send_message_to_queue(
            command="dbsub",
            chat_id=update.effective_chat.id,
            message_text=message_string,
        )
    return ConversationHandler.END

  @classmethod
  async def handle_reply(
      cls,
      update: Update,
      context: CallbackContext
  ):
    """Handles replies to quiz prompts.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.message.reply_to_message:
      user = update.message.from_user
      message_text = update.message.text
      username = user.username
      message_id = update.message.reply_to_message.message_id
      message_object = {
          "text": message_text,
          "username": username,
          "message_id": message_id,
      }
      message_string = json.dumps(message_object)
      await cls.send_message_to_queue(
          command="quiz_answer",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )

  @classmethod
  async def handle_bulk_unsubscribe(
      cls,
      update: Update,
      context: CallbackContext
  ) -> int:
    """Processes the input for unsubscribing from deckboxes.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      A conversation handler that stops the conversation with the user
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      user_input = update.message.text
      lines = user_input.split("\n")
      for line in lines:
        message_object = {
            "telegram": username,
            "deckbox": line,
        }
        message_string = json.dumps(message_object)
        await cls.send_message_to_queue(
            command="dbunsub",
            chat_id=update.effective_chat.id,
            message_text=message_string,
        )
    return ConversationHandler.END

  @classmethod
  async def handle_bulk_card_search(
      cls,
      update: Update,
      context: CallbackContext
  ) -> int:
    """Processes the input for searchng for cards.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      A conversation handler that stops the conversation with the user
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      user_input = update.message.text
      lines = user_input.split("\n")
      message_object = {
            "telegram": username,
            "cards": lines,
        }
      message_string = json.dumps(message_object)
      await cls.send_message_to_queue(
          command="search",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
      await update.message.reply_text("Searching...")
    return ConversationHandler.END

  @classmethod
  async def wishlist_search_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles searching for cards in user's wishlist.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      await cls.send_message_to_queue(
          command="wish",
          chat_id=update.effective_chat.id,
          message_text=username,
      )
      await update.message.reply_text("Searching...")

  @classmethod
  async def cancel_conversation(
      cls,
      update: Update,
      context: CallbackContext,
  ) -> ConversationHandler.END:
    """Cancels the conversation manually.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      A conversation handler that stops the conversation with the user
    """
    user = update.message.from_user
    username = user.username
    await cls.send_message_to_queue(
        command="start",
        chat_id=update.effective_chat.id,
        message_text=username,
    )
    return ConversationHandler.END

  @classmethod
  async def send_image_to_user(
      cls,
      chat_id: str,
      image_url: str,
  ) -> None:
    """Sends an image to a user.

    Args:
      chat_id: id of the chat with the user
      image_url: url of the image that will be sent to the user
    """
    await cls.bot.send_photo(chat_id=chat_id, photo=image_url)

  @classmethod
  async def send_quiz_image_to_chat(
      cls,
      chat_id: str,
      card_name: str,
      image_url: str,
  ) -> None:
    """Sends an quiz image to chat and adds it to mongo db.

    Args:
      chat_id: id of the chat with the user
      image_url: url of the image that will be sent to the user
    """
    reply = await cls.bot.send_photo(chat_id=chat_id, photo=image_url)
    reply_message_id = reply.message_id
    await MongoClient.add_quiz_object(
        card_name=card_name,
        message_id=reply_message_id,
    )

  @classmethod
  async def send_message_to_queue(
      cls,
      command: str,
      chat_id: str,
      message_text: str,
  ) -> None:
    """Sends a message to a "from-user" rabbitmq queue.

    Args:
      command: name of the command that should be processed
      chat_id: id of the chat with the user
      message_text: message that will be sent to the user
    """
    message = Utils.generate_outgoing_message(
        command=command,
        chat_id=chat_id,
        message_text=message_text,
    )
    connection = await connect_robust(**config.AIO_PIKA_PARAMETERS)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        name="bot-exchange",
        type=ExchangeType.DIRECT,
    )
    await exchange.publish(
        message=Message(body=message),
        routing_key=config.FROM_USER_QUEUE_NAME,
    )
    await connection.close()

  @classmethod
  async def any_message_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to any private message to the bot.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    await cls.send_message_to_queue(
        command="help",
        chat_id=update.effective_chat.id,
        message_text="",
    )

  @classmethod
  async def edh_danas_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles creating a EDH danas poll.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    chat_type = ""
    if update.effective_chat.type == "private":
      chat_type = "private"
    else:
      chat_type = "group"
    message_object = {
        "message": "EDH danas?",
        "options": ["Da", "Ne", "Ne znam"],
        "chat_type": chat_type,
    }
    message_string = json.dumps(message_object)
    await cls.send_message_to_queue(
        command="edhdanas",
        chat_id=update.effective_chat.id,
        message_text=message_string,
    )

  @classmethod
  async def user_registration_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to a private message with /reg command and sends
    a corresponding message to the "from-user" queue.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      await cls.send_message_to_queue(
          command="reg",
          chat_id=update.effective_chat.id,
          message_text=username,
      )

  @classmethod
  async def deckbox_adding_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> ConversationHandler.END:
    """Handles user input when adding deckbox account.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      A conversation handler that stops the conversation with the user
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      deckbox = update.message.text
      message_object = {
          "telegram": username,
          "deckbox": deckbox,
      }
      message_string = json.dumps(message_object)
      await cls.send_message_to_queue(
          command="regdeckbox",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
      return ConversationHandler.END

  @classmethod
  async def deckbox_check_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles user checking their deckbox.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      await cls.send_message_to_queue(
          command="mydeckbox",
          chat_id=update.effective_chat.id,
          message_text=username,
      )

  @classmethod
  async def deckbox_update_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler user updating their deckbox.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      await cls.send_message_to_queue(
          command="updatedeckbox",
          chat_id=update.effective_chat.id,
          message_text=username,
      )

  @classmethod
  async def deckbox_subscriptions_check_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles user checking their current subscriptions list.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      await cls.send_message_to_queue(
          command="mydeckboxsubs",
          chat_id=update.effective_chat.id,
          message_text=username,
      )

  @classmethod
  async def card_image_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to any message with /ci command and sends a 
    corresponding message to the "from-user" queue.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    message_text = update.message.text
    split_message = message_text.split("/ci ")
    if len(split_message) < 2:
      return
    card_name = split_message[1]
    print(f"Received a /ci command with text: {card_name}")
    await cls.send_message_to_queue(
        command="ci",
        chat_id=update.effective_chat.id,
        message_text=card_name,
    )

  @classmethod
  async def card_quiz_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to any message with /quiz command and sends a 
    corresponding message to the "from-user" queue.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    await cls.send_message_to_queue(
        command="quiz",
        chat_id=update.effective_chat.id,
        message_text="",
    )

  @classmethod
  async def card_url_hanlder(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to any message with /c command and sends a 
    corresponding message to the "from-user" queue.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    message_text = update.message.text
    split_message = message_text.split("/c ")
    if len(split_message) < 2:
      return
    card_name = split_message[1]
    await cls.send_message_to_queue(
        command="c",
        chat_id=update.effective_chat.id,
        message_text=card_name,
    )

  @classmethod
  async def card_price_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to any message with /cp command and sends a 
    corresponding message to the "from-user" queue.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    message_text = update.message.text
    split_message = message_text.split("/cp ")
    if len(split_message) < 2:
      return
    card_name = split_message[1]
    await cls.send_message_to_queue(
        command="cp",
        chat_id=update.effective_chat.id,
        message_text=card_name,
    )

  @classmethod
  def run_bot(cls):
    """A function that creates command handlers and runs the bot.
    """
    deckbox_bulk_subscribe_handler = ConversationHandler(
        entry_points=[CommandHandler("dbsub", cls.start_bulk_subsribe)],
        states={cls.input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_bulk_subscribe)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    deckbox_bulk_unsubscribe_handler = ConversationHandler(
        entry_points=[CommandHandler("dbunsub", cls.start_bulk_unsubsribe)],
        states={cls.input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_bulk_unsubscribe)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    deckbox_register_handler = ConversationHandler(
        entry_points=[CommandHandler("regdeckbox", cls.start_deckbox_register)],
        states={cls.input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.deckbox_adding_handler)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    card_search_handler = ConversationHandler(
        entry_points=[CommandHandler("search", cls.start_bulk_card_search)],
        states={cls.input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_bulk_card_search)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    app = ApplicationBuilder().token(token=config.BOT_TOKEN).build()
    app.add_handler(deckbox_bulk_subscribe_handler)
    app.add_handler(deckbox_bulk_unsubscribe_handler)
    app.add_handler(deckbox_register_handler)
    app.add_handler(card_search_handler)
    app.add_handler(CommandHandler("c", cls.card_url_hanlder))
    app.add_handler(CommandHandler("cp", cls.card_price_handler))
    app.add_handler(CommandHandler("ci", cls.card_image_handler))
    app.add_handler(CommandHandler("quiz", cls.card_quiz_handler))
    app.add_handler(CommandHandler("reg", cls.user_registration_handler))
    app.add_handler(CommandHandler("mydeckbox", cls.deckbox_check_handler))
    app.add_handler(CommandHandler("updatedeckbox", cls.deckbox_update_handler))
    app.add_handler(CommandHandler("edhdanas", cls.edh_danas_handler))
    app.add_handler(CommandHandler("wish", cls.wishlist_search_handler))
    app.add_handler(CommandHandler("help", cls.any_message_handler))
    app.add_handler(CommandHandler(
        "mydeckboxsubs",
        cls.deckbox_subscriptions_check_handler,
    ))
    app.add_handler(MessageHandler(
        filters=filters.REPLY,
        callback=cls.handle_reply,
    ))
    app.add_handler(MessageHandler(
        filters=filters.TEXT,
        callback=cls.start_with_keyboard,
    ))

    while True:
      try:
        print("Starting bot")
        app.run_polling()
      except Exception as e:
        print(e)
        time.sleep(5)


if __name__ == "__main__":
  MagicBot.run_bot()