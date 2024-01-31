"""Module for running the telegram bot.
"""
import asyncio
import json
import time
from datetime import datetime
from aio_pika import (connect_robust, ExchangeType, Message)
from telegram import (
    Bot,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
    CallbackQueryHandler,
)
from telegram import ReplyKeyboardRemove
from bot.config import config
from bot.utils.utils import Utils
from bot.mongo.mongo_client import MongoClient

class MagicBot:
  bot = Bot(token=config.BOT_TOKEN)
  search_input = 0
  dbsearch_input = 0
  consearch_input = 0
  dbwish_input = 0
  dbsub_input = 0
  dbunsub_input = 0
  dbreg_input = 0
  db_names, card_list = range(2)
  # League stuff
  league_register_input = 0
  league_game_register_input = 0
  league_id, league_user = range(2)
  league_for_match_choice = 0


  @classmethod
  async def league_standings_choice_inline_menu(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Creates a menu with leagues for player league standings choice.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    keyboard = []
    # Get user leagues
    player_data = await MongoClient.get_all_leagues_for_player(
        telegram=f"@{username}"
    )
    for data in player_data:
      league_name = data.get("league_name")
      league_id = data.get("league_id")
      callback_data = f"lsc_{league_id}"
      keyboard.append([InlineKeyboardButton(
          text=league_name, callback_data=callback_data)
      ])
    keyboard.append([InlineKeyboardButton(
          text="Cancel", callback_data="cancel")
      ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="Please choose a league:",
        reply_markup=reply_markup,
    )

  @classmethod
  async def league_matches_choice_inline_menu(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Creates a menu with leagues for matches statistics choice.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    keyboard = []
    # Get user leagues
    player_data = await MongoClient.get_all_leagues_for_player(
        telegram=f"@{username}"
    )
    for data in player_data:
      league_name = data.get("league_name")
      league_id = data.get("league_id")
      callback_data = f"lmc_{league_id}"
      keyboard.append([InlineKeyboardButton(
          text=league_name, callback_data=callback_data)
      ])
    keyboard.append([InlineKeyboardButton(
          text="Cancel", callback_data="cancel")
      ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="Please choose a league:",
        reply_markup=reply_markup,
    )

  @classmethod
  async def league_stats_choice_inline_menu(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Creates a menu with leagues for stats choice.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    keyboard = []
    # Get user leagues
    player_data = await MongoClient.get_all_leagues_for_player(
        telegram=f"@{username}"
    )
    for data in player_data:
      league_name = data.get("league_name")
      league_id = data.get("league_id")
      callback_data = f"llc_{league_id}"
      keyboard.append([InlineKeyboardButton(
          text=league_name, callback_data=callback_data)
      ])
    keyboard.append([InlineKeyboardButton(
          text="Cancel", callback_data="cancel")
      ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="Please choose a league:",
        reply_markup=reply_markup,
    )

  @classmethod
  async def league_match_choice_inline_menu(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Creates a menu with leagues for match choice.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    keyboard = []
    # Get user leagues
    player_data = await MongoClient.get_all_leagues_for_player(
        telegram=f"@{username}"
    )
    for data in player_data:
      league_name = data.get("league_name")
      league_id = data.get("league_id")
      callback_data = f"league_for_match_choice_{league_id}"
      keyboard.append([InlineKeyboardButton(
          text=league_name, callback_data=callback_data)
      ])
    keyboard.append([InlineKeyboardButton(
          text="Cancel", callback_data="cancel")
      ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="Please choose a league:",
        reply_markup=reply_markup,
    )

  @classmethod
  async def button(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ):
    """Handles user pressing buttons in inline keyboards.
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    username = user.username
    # Cance;]l
    if query.data.startswith("cancel"):
      await query.edit_message_text(
          text="Command canceled"
      )
      await cls.send_message_to_queue(
          command="leaguemenu",
          chat_id=update.effective_chat.id,
          message_text=username,
      )
    # League for match recording
    elif query.data.startswith("league_for_match_choice_"):
      league_id = query.data.split("league_for_match_choice_")[1]
      context.user_data["league_for_match_choice"] = league_id
      await query.edit_message_text(
          text="League chosen"
      )
      full_text = (
          "Please enter your opponent's telegram account name.\n"
          "To cancel the command type /cancel.\n"
      )
      all_players = await MongoClient.get_all_leagues_players(
          league_id=league_id,
      )
      keyboard = []
      for player in all_players:
        if player != f"@{username}":
          keyboard.append([f"{player.get("telegram")}"])
      reply_markup = ReplyKeyboardMarkup(
          keyboard,
          resize_keyboard=True,
      )
      await context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=full_text,
          reply_markup=reply_markup,
      )
      return cls.league_for_match_choice
    # League result submitting
    elif query.data.startswith("lr_"):
      match_result = query.data[3:]
      "lr_{league_id}%{username}%0-2%{user_input}"
      all_res = match_result.split("%")
      message_object = {
        "league_id": all_res[0],
        "player_one": all_res[1],
        "player_two": all_res[3],
        "result": all_res[2],
      }
      message_string = json.dumps(message_object)
      await query.edit_message_text(
          text="League match result pending"
      )
      await cls.send_message_to_queue(
          command="leaguemenu",
          chat_id=update.effective_chat.id,
          message_text=username,
      )
      await cls.send_message_to_queue(
          command="league_match_result_send",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
    # League result confirmation
    elif query.data.startswith("lryes_"):
      result_string = query.data[6:]
      all_res = result_string.split("%")
      message_object = {
        "league_id": all_res[0],
        "player_one": all_res[1],
        "player_two": all_res[3],
        "result": all_res[2],
      }
      message_string = json.dumps(message_object)
      await query.edit_message_text(
          text="Thanks for confirming the result!"
      )
      await cls.send_message_to_queue(
          command="league_match_result_confirm",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
    # League standings confirmation
    elif query.data.startswith("lsc_"):
      result_string = query.data[4:]
      await query.edit_message_text(
          text="League chosen"
      )
      message_object = {
          "league_id": result_string,
          "telegram": f"@{username}",
      }
      message_string = json.dumps(message_object)
      await cls.send_message_to_queue(
          command="league_standings_check",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
    # League stats confirmation
    elif query.data.startswith("llc_"):
      result_string = query.data[4:]
      await query.edit_message_text(
          text="League chosen"
      )
      message_object = {
          "league_id": result_string,
          "telegram": f"@{username}",
      }
      message_string = json.dumps(message_object)
      await cls.send_message_to_queue(
          command="league_stats_check",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
    # League stats confirmation
    elif query.data.startswith("lmc_"):
      result_string = query.data[4:]
      await query.edit_message_text(
          text="League chosen"
      )
      message_object = {
          "league_id": result_string,
          "telegram": f"@{username}",
      }
      message_string = json.dumps(message_object)
      await cls.send_message_to_queue(
          command="league_matches_check",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )

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
  async def deckbox_menu_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Handles user switching to a deckbox menu.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    user = update.message.from_user
    username = user.username
    await cls.send_message_to_queue(
        command="deckboxmenu",
        chat_id=update.effective_chat.id,
        message_text=username,
    )

  @classmethod
  async def conflux_menu_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Handles user switching to a conflux menu.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    user = update.message.from_user
    username = user.username
    await cls.send_message_to_queue(
        command="confluxmenu",
        chat_id=update.effective_chat.id,
        message_text=username,
    )

  @classmethod
  async def league_menu_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> None:
    """Handles user switching to a league menu.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    user = update.message.from_user
    username = user.username
    await cls.send_message_to_queue(
        command="leaguemenu",
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
      registered: check if the user is registered,
      disable_preview: check if the url previews should be disabled
    """
    keyboard = [["/reg",]]
    if registered:
      keyboard = [
          ["/search", "/wish"],
          ["/deckbox", "/conflux"],
          ["/league", "/help"],
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
  async def send_deckbox_menu_to_user(
      cls,
      chat_id: str,
      message: str,
      registered: bool,
      disable_preview: bool = True,
  ) -> None:
    """Sends a deckbox menu to a user.

    Args:
      chat_id: id of the chat with the user
      message: message that will be sent to the user
      registered: check if the user is registered,
      disable_preview: check if the url previews should be disabled
    """
    keyboard = [["/reg",]]
    if registered:
      keyboard = [
          ["/dbsearch", "/dbwish"],
          ["/dbsub", "/dbunsub"],
          ["/regdeckbox", "/updatedeckbox"],
          ["/mydeckbox", "/mydeckboxsubs"],
          ["/main", "/dbhelp"],
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
  async def send_conflux_menu_to_user(
      cls,
      chat_id: str,
      message: str,
      registered: bool,
      disable_preview: bool = True,
  ) -> None:
    """Sends a conflux menu to a user.

    Args:
      chat_id: id of the chat with the user
      message: message that will be sent to the user
      registered: check if the user is registered,
      disable_preview: check if the url previews should be disabled
    """
    keyboard = [["/reg",]]
    if registered:
      keyboard = [
          ["/consearch", "/conwish"],
          ["/confluxsub", "/confluxunsub"],
          ["/main", "/confluxhelp"],
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
  async def send_league_menu_to_user(
      cls,
      chat_id: str,
      message: str,
      registered: bool,
      disable_preview: bool = True,
  ) -> None:
    """Sends a league menu to a user.

    Args:
      chat_id: id of the chat with the user
      message: message that will be sent to the user
      registered: check if the user is registered,
      disable_preview: check if the url previews should be disabled
    """
    keyboard = [["/reg",]]
    if registered:
      keyboard = [
          ["/match"],
          ["/mystandings", "/mymatches"],
          ["/leaguereg", "/leaderboards"],
          ["/main", "/leaguehelp"],
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
  async def send_league_match_confirmation_to_user(
      cls,
      chat_id: str,
      message: str,
      disable_preview: bool = True,
  ) -> None:
    """Sends a match confirmation to user.

    Args:
      chat_id: id of the chat with the user
      message: message that will be sent to the user
      registered: check if the user is registered,
      disable_preview: check if the url previews should be disabled
    """
    full_message = message.split("\n")
    callback_string = f"lryes_{full_message[0]}"
    message_text = "\n".join(full_message[1:])
    keyboard = [[
      InlineKeyboardButton(
          text="Yes",
          callback_data=callback_string),
      InlineKeyboardButton(
          text="No",
          callback_data="cancel"),
      ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await cls.bot.send_message(
        chat_id=chat_id,
        text=message_text,
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
    return cls.dbsub_input

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
    return cls.search_input

  @classmethod
  async def start_conflux_search(
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
    return cls.consearch_input

  @classmethod
  async def start_db_card_search(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> int:
    """Handles opening the input for searching cards with dbsearch.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    result_text = (
      "Please enter the list of deckboxes to look for cards in.\n"
      "Each deckbox name must be on a separate line.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.db_names

  @classmethod
  async def start_db_wish(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> int:
    """Handles opening the input for entering deckbox names with dbwish.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    result_text = (
      "Please enter the list of deckbox names to look for cards in.\n"
      "Each deckbox name must be on a separate line.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.dbwish_input

  @classmethod
  async def handle_db_names_list(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> int:
    """Handles opening the input selecting cards after user entered db names.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    context.user_data['db_names'] = update.message.text
    result_text = (
      "Please enter the list of cards to look for.\n"
      "Each card must be on a separate line.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.card_list

  @classmethod
  async def handle_db_search(
      cls,
      update: Update,
      context: CallbackContext
  ) -> int:
    """Processes the input for searchng for cards in specific deckboxes.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      A conversation handler that stops the conversation with the user
    """
    context.user_data['card_list'] = update.message.text
    db_names = context.user_data['db_names']
    card_list = context.user_data['card_list']
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      cards = card_list.split("\n")
      deckboxes = db_names.split("\n")
      message_object = {
            "telegram": username,
            "cards": cards,
            "deckboxes": deckboxes,
        }
      message_string = json.dumps(message_object)
      await update.message.reply_text("Searching...")
      await cls.send_message_to_queue(
          command="dbsearch",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
    return ConversationHandler.END

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
    return cls.dbunsub_input

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
    return cls.dbreg_input

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
      lines = [line.strip() for line in user_input.split("\n")]
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
      lines = [line.strip() for line in user_input.split("\n")]
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
      lines = [line.strip() for line in user_input.split("\n")]
      message_object = {
            "telegram": username,
            "cards": lines,
            "search": "all",
        }
      message_string = json.dumps(message_object)
      await update.message.reply_text("Searching...")
      user_store_subs = await MongoClient.get_user_store_subscriptions(
          telegram=f"@{username}"
      )
      if user_store_subs and "conflux" in user_store_subs:
        await cls.send_message_to_queue(
            command="consearch",
            chat_id=update.effective_chat.id,
            message_text=message_string,
        )
        await asyncio.sleep(len(lines) / 10)
      await cls.send_message_to_queue(
          command="search",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
    return ConversationHandler.END

  @classmethod
  async def handle_conflux_card_search(
      cls,
      update: Update,
      context: CallbackContext
  ) -> int:
    """Processes the input for searchng for cards in conflux.

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
      lines = [line.strip() for line in user_input.split("\n")]
      message_object = {
            "telegram": username,
            "cards": lines,
            "search": "conflux",
        }
      message_string = json.dumps(message_object)
      await update.message.reply_text("Searching...")
      await cls.send_message_to_queue(
          command="consearch",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
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
      message_object = {
          "telegram": username,
          "search": "main",
      }
      message_string = json.dumps(message_object)
      await update.message.reply_text("Searching...")
      user_store_subs = await MongoClient.get_user_store_subscriptions(
          telegram=f"@{username}"
      )
      if user_store_subs and "conflux" in user_store_subs:
        # Get the length of the wishlist
        user_data = await MongoClient.get_user_data(telegram=f"@{username}")
        deckbox = user_data.get("deckbox_name")
        wishlist_id = await MongoClient.get_deckbox_id(
            deckbox_name=deckbox,
            wishlist=True,
        )
        wishlist_cards_dict = await MongoClient.get_deckbox_cards_dict(
            deckbox_id=wishlist_id,
            wishlist=True,
        )
        await cls.send_message_to_queue(
            command="conwish",
            chat_id=update.effective_chat.id,
            message_text=username,
        )
        await asyncio.sleep(len(wishlist_cards_dict) / 20)
      await cls.send_message_to_queue(
          command="wish",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )

  @classmethod
  async def deckbox_wishlist_search_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles searching for cards in user's wishlist in specific deckboxes.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      user_input = update.message.text
      lines = [line.strip() for line in user_input.split("\n")]
      username = user.username
      message_object = {
          "telegram": username,
          "search": "deckbox",
          "deckboxes": lines,
      }
      message_string = json.dumps(message_object)
      await update.message.reply_text("Searching...")
      await cls.send_message_to_queue(
          command="dbwish",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
      return ConversationHandler.END

  @classmethod
  async def conflux_wishlist_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles searching for cards in user's wishlist in conflux.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      await update.message.reply_text("Searching...")
      await cls.send_message_to_queue(
          command="conwish",
          chat_id=update.effective_chat.id,
          message_text=username,
      )

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
  async def ru_mtg_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds with a list of ru-mtg deckboxes.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    rumtg = (
        "anahoret\n"
        "buttelius\n"
        "alexgaidukov\n"
        "alexey_g\n"
        "sathonyx\n"
        "alexvoron\n"
        "chieftain\n"
        "nekromancer\n"
        "macros013\n"
        "crazyfen\n"
        "skyhound\n"
        "hmchk\n"
        "rid42\n"
        "1ndifferent\n"
    )
    await update.message.reply_text(rumtg)

  @classmethod
  async def deckbox_help_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to /dbhelp command.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    await cls.send_message_to_queue(
        command="dbhelp",
        chat_id=update.effective_chat.id,
        message_text="",
    )

  @classmethod
  async def conflux_help_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to /confluxhelp command.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    await cls.send_message_to_queue(
        command="confluxhelp",
        chat_id=update.effective_chat.id,
        message_text="",
    )

  @classmethod
  async def league_help_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to /leaguehelp command.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    await cls.send_message_to_queue(
        command="leaguehelp",
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
  async def admin_check_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to any message with /admin command and sends a
    message to the user if they are an admin.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username in config.ADMINS:
      await update.message.reply_text("You are an admin!")

  @classmethod
  async def deckbox_recache_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that manually re-caches all deckboxes (admin only).

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    await cls.send_message_to_queue(
        command="deckboxrecache",
        chat_id=update.effective_chat.id,
        message_text="whatever",
    )

  @classmethod
  async def conflux_cache_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that manually caches conflux store (admin only).

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    await cls.send_message_to_queue(
        command="confluxcache",
        chat_id=update.effective_chat.id,
        message_text="whatever",
    )

  @classmethod
  async def store_add_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that responds to any message with /addstore command and sends a 
    corresponding message to the "from-user" queue

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    message_text = update.message.text
    split_message = message_text.split("/addstore ")
    if len(split_message) < 2:
      return
    store_name = split_message[1]
    await cls.send_message_to_queue(
        command="addstore",
        chat_id=update.effective_chat.id,
        message_text=store_name,
    )

  @classmethod
  async def conflux_subscribe_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles user subscribing to conflux store.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    user = update.message.from_user
    username = user.username
    message_object = {
        "telegram": username,
        "store": "conflux",
    }
    message_string = json.dumps(message_object)
    await cls.send_message_to_queue(
        command="confluxsub",
        chat_id=update.effective_chat.id,
        message_text=message_string,
    )

  @classmethod
  async def conflux_unsub_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles user unsubscribing from conflux store.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    user = update.message.from_user
    username = user.username
    message_object = {
        "telegram": username,
        "store": "conflux",
    }
    message_string = json.dumps(message_object)
    await cls.send_message_to_queue(
        command="confluxunsub",
        chat_id=update.effective_chat.id,
        message_text=message_string,
    )

  @classmethod
  async def league_start_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles admin starting a new league.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    message_text = update.message.text
    split_message = message_text.split("/leaguestart ")
    if len(split_message) < 2:
      return
    league = split_message[1].split(" ")
    if len(league) < 2:
      return
    league_name = " ".join(league[1:])
    league_length = int(league[0])
    message_object = {
        "league_name": league_name,
        "league_length": league_length,
    }
    message_string = json.dumps(message_object)
    await cls.send_message_to_queue(
        command="league_create",
        chat_id=update.effective_chat.id,
        message_text=message_string,
    )

  @classmethod
  async def league_status_change_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles admin changing status of the league.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type != "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    message_text = update.message.text
    split_message = message_text.split("/leaguestatus ")
    if len(split_message) < 2:
      return
    league = split_message[1].split(" ")
    if len(league) < 2:
      return
    league_id = " ".join(league[1:])
    status = league[0].lower() == "true"
    message_object = {
        "league_id": league_id,
        "status": status,
    }
    message_string = json.dumps(message_object)
    await cls.send_message_to_queue(
        command="league_status_change",
        chat_id=update.effective_chat.id,
        message_text=message_string,
    )

  @classmethod
  async def league_subscribe_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles admin subscribing a channel to league messages.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    message_text = update.message.text
    split_message = message_text.split("/leaguesub ")
    if len(split_message) < 2:
      return
    league_id = split_message[1]
    message_object = {
          "league_id": league_id,
          "chat_id": update.effective_chat.id,
      }
    message_string = json.dumps(message_object)
    await cls.send_message_to_queue(
        command="league_subscribe",
        chat_id=update.effective_chat.id,
        message_text=message_string,
    )

  @classmethod
  async def league_unsubscribe_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles admin unsubscribing a channel from league messages.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    message_text = update.message.text
    split_message = message_text.split("/leagueunsub ")
    if len(split_message) < 2:
      return
    league_id = split_message[1]
    message_object = {
          "league_id": league_id,
          "chat_id": update.effective_chat.id,
      }
    message_string = json.dumps(message_object)
    await cls.send_message_to_queue(
        command="league_unsubscribe",
        chat_id=update.effective_chat.id,
        message_text=message_string,
    )

  @classmethod
  async def league_add_invite_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handles creating a new invite for the league.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    message_text = update.message.text
    split_message = message_text.split("/invite ")
    if len(split_message) < 2:
      return
    league_id = split_message[1]
    await cls.send_message_to_queue(
        command="league_invite",
        chat_id=update.effective_chat.id,
        message_text=league_id,
    )

  @classmethod
  async def start_league_user_reg(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> int:
    """Handles opening the input for registering a user in a league.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    result_text = (
      "Please enter the ID of the league.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.league_id

  @classmethod
  async def handle_league_id(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE,
  ) -> int:
    """Handles opening the input for league ID.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      An input ID
    """
    if update.effective_chat.type != "private":
      return
    context.user_data['league_id'] = update.message.text
    result_text = (
      "Please enter your registration ID.\n"
      "To cancel the command type /cancel.\n"
    )
    await update.message.reply_text(
        result_text,
        reply_markup=ReplyKeyboardRemove(),
    )
    return cls.league_user

  @classmethod
  async def handle_league_user_register_id(
      cls,
      update: Update,
      context: CallbackContext
  ) -> int:
    """Processes the input for searchng for registering user.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      A conversation handler that stops the conversation with the user
    """
    context.user_data['league_user'] = update.message.text
    league_id = context.user_data['league_id']
    league_user = context.user_data['league_user']
    if update.effective_chat.type == "private":
      user = update.message.from_user
      username = user.username
      message_object = {
            "telegram": f"@{username}",
            "chat_id": update.effective_chat.id,
            "league_id": league_id,
            "league_user": league_user,
        }
      message_string = json.dumps(message_object)
      await cls.send_message_to_queue(
          command="league_user_reg",
          chat_id=update.effective_chat.id,
          message_text=message_string,
      )
    return ConversationHandler.END

  @classmethod
  async def handle_player_choice(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ):
    """Processes the input of user choosing match result.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    Returns:
      A conversation handler that stops the conversation with the user
    """
    user_input = update.message.text
    league_id = context.user_data.get('league_for_match_choice')
    user = update.message.from_user
    username = user.username
    user_exists = await MongoClient.get_league_player(
        telegram=user_input,
        league_id=league_id,
    )
    if not user_exists:
      await context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=f"Player {user_input} not found in this league",
      )
      await cls.send_message_to_queue(
          command="leaguemenu",
          chat_id=update.effective_chat.id,
          message_text=username,
      )
      return ConversationHandler.END
    if f"@{username}" == user_input:
      await context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=f"Don't play with yourself!",
      )
      await cls.send_message_to_queue(
          command="leaguemenu",
          chat_id=update.effective_chat.id,
          message_text=username,
      )
      return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(
          text="2-0 (you won)",
          callback_data=f"lr_{league_id}%@{username}%2-0%{user_input}")
      ],
      [InlineKeyboardButton(
          text="2-1 (you won)",
          callback_data=f"lr_{league_id}%@{username}%2-1%{user_input}")
      ],
      [InlineKeyboardButton(
          text="1-2 (you lost)",
          callback_data=f"lr_{league_id}%@{username}%1-2%{user_input}")
      ],
      [InlineKeyboardButton(
          text="0-2 (you lost)",
          callback_data=f"lr_{league_id}%@{username}%0-2%{user_input}")
      ],
      [InlineKeyboardButton(
          text="Cancel",
          callback_data="cancel")
      ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f'Choose your result against {user_input}:\n',
        reply_markup=reply_markup,
    )
    return ConversationHandler.END

  @classmethod
  async def league_update_handler(
      cls,
      update: Update,
      context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handler that manually updates all leagues.

    Args:
      update: telegram-bot parameter
      context: telegram-bot parameter
    """
    if not update.effective_chat.type == "private":
      return
    user = update.message.from_user
    username = user.username
    if username not in config.ADMINS:
      return
    await cls.send_message_to_queue(
        command="leagues_update",
        chat_id=update.effective_chat.id,
        message_text="whatever",
    )

  @classmethod
  def run_bot(cls):
    """A function that creates command handlers and runs the bot.
    """
    deckbox_bulk_subscribe_handler = ConversationHandler(
        entry_points=[CommandHandler("dbsub", cls.start_bulk_subsribe)],
        states={cls.dbsub_input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_bulk_subscribe)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    deckbox_bulk_unsubscribe_handler = ConversationHandler(
        entry_points=[CommandHandler("dbunsub", cls.start_bulk_unsubsribe)],
        states={cls.dbunsub_input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_bulk_unsubscribe)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    deckbox_register_handler = ConversationHandler(
        entry_points=[CommandHandler("regdeckbox", cls.start_deckbox_register)],
        states={cls.dbreg_input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.deckbox_adding_handler)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    card_search_handler = ConversationHandler(
        entry_points=[CommandHandler("search", cls.start_bulk_card_search)],
        states={cls.search_input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_bulk_card_search)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    conflux_search_handler = ConversationHandler(
        entry_points=[CommandHandler("consearch", cls.start_conflux_search)],
        states={cls.consearch_input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_conflux_card_search)]
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    deckbox_search_handler = ConversationHandler(
        entry_points=[CommandHandler("dbsearch", cls.start_db_card_search)],
        states={
        cls.db_names: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_db_names_list
        )],
        cls.card_list: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_db_search
        )],
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    deckbox_wish_handler = ConversationHandler(
        entry_points=[CommandHandler("dbwish", cls.start_db_wish)],
        states={cls.dbwish_input: [MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            cls.deckbox_wishlist_search_handler
        )]},
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    # League stuff
    league_register_handler = ConversationHandler(
        entry_points=[CommandHandler("leaguereg", cls.start_league_user_reg)],
        states={
        cls.db_names: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_league_id
        )],
        cls.card_list: [MessageHandler(
            filters.TEXT & ~filters.COMMAND, cls.handle_league_user_register_id
        )],
        },
        fallbacks=[CommandHandler("cancel", cls.cancel_conversation)]
    )
    league_match_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            cls.button,
            pattern='^league_for_match_choice_')],
        states={
            cls.league_for_match_choice: [
              MessageHandler(
                filters.TEXT & ~filters.COMMAND, cls.handle_player_choice
                )
            ]
        },
        fallbacks=[CommandHandler('cancel', cls.cancel_conversation)]
    )
    app = ApplicationBuilder().token(token=config.BOT_TOKEN).build()
    app.add_handler(league_match_handler)
    app.add_handler(CallbackQueryHandler(cls.button))
    app.add_handler(deckbox_bulk_subscribe_handler)
    app.add_handler(deckbox_bulk_unsubscribe_handler)
    app.add_handler(deckbox_register_handler)
    app.add_handler(card_search_handler)
    app.add_handler(conflux_search_handler)
    app.add_handler(deckbox_search_handler)
    app.add_handler(deckbox_wish_handler)
    app.add_handler(league_register_handler)
    app.add_handler(CommandHandler("c", cls.card_url_hanlder))
    app.add_handler(CommandHandler("cp", cls.card_price_handler))
    app.add_handler(CommandHandler("ci", cls.card_image_handler))
    app.add_handler(CommandHandler("quiz", cls.card_quiz_handler))
    app.add_handler(CommandHandler("reg", cls.user_registration_handler))
    app.add_handler(CommandHandler("mydeckbox", cls.deckbox_check_handler))
    app.add_handler(CommandHandler("updatedeckbox", cls.deckbox_update_handler))
    app.add_handler(CommandHandler("edhdanas", cls.edh_danas_handler))
    app.add_handler(CommandHandler("wish", cls.wishlist_search_handler))
    app.add_handler(CommandHandler("conwish", cls.conflux_wishlist_handler))
    app.add_handler(CommandHandler("help", cls.any_message_handler))
    app.add_handler(CommandHandler("rumtg", cls.ru_mtg_handler))
    app.add_handler(CommandHandler("dbhelp", cls.deckbox_help_handler))
    app.add_handler(CommandHandler("main", cls.start_with_keyboard))
    app.add_handler(CommandHandler("deckbox", cls.deckbox_menu_handler))
    app.add_handler(CommandHandler("admin", cls.admin_check_handler))
    app.add_handler(CommandHandler("addstore", cls.store_add_handler))
    app.add_handler(CommandHandler("dbrecache", cls.deckbox_recache_handler))
    # Conflux
    app.add_handler(CommandHandler("conflux", cls.conflux_menu_handler))
    app.add_handler(CommandHandler("confluxsub", cls.conflux_subscribe_handler))
    app.add_handler(CommandHandler("confluxunsub", cls.conflux_unsub_handler))
    app.add_handler(CommandHandler("confluxcache", cls.conflux_cache_handler))
    app.add_handler(CommandHandler("confluxhelp", cls.conflux_help_handler))
    # League
    app.add_handler(CommandHandler(
        "leaguestatus", cls.league_status_change_handler)
    )
    app.add_handler(CommandHandler("leaguesub", cls.league_subscribe_handler))
    app.add_handler(CommandHandler(
        "leagueunsub", cls.league_unsubscribe_handler)
    )
    app.add_handler(CommandHandler("leaguesupdate", cls.league_update_handler))
    app.add_handler(CommandHandler("league", cls.league_menu_handler))
    app.add_handler(CommandHandler("leaguestart", cls.league_start_handler))
    app.add_handler(CommandHandler("invite", cls.league_add_invite_handler))
    app.add_handler(CommandHandler("leaguehelp", cls.league_help_handler))
    app.add_handler(CommandHandler(
        "mystandings", cls.league_standings_choice_inline_menu)
    )
    app.add_handler(CommandHandler(
        "mymatches", cls.league_matches_choice_inline_menu)
    )
    app.add_handler(CommandHandler(
        "leaderboards", cls.league_stats_choice_inline_menu)
    )
    app.add_handler(CommandHandler(
        "match", cls.league_match_choice_inline_menu)
    )
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