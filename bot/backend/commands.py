"""Module for resolving commands sent by from-user-listener.
"""
import json
from bot.deckbox.deckbox import Deckbox
from bot.scryfall.scryfall import ScryfallFetcher
from bot.mongo.mongo_client import MongoClient
from bot.utils.utils import Utils
from bot.deckbox.deckbox import Deckbox
from bot.backend.backend import Backend
from bot.league.league import League
from datetime import datetime

class TelegramCommands:

  @classmethod
  async def send_freeform_message(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a freeform message to chat.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with card name
    Returns:
      A dict with message encoded into bytes
    """
    return Utils.generate_outgoing_message(
        command="text",
        chat_id=chat_id,
        message_text=message_text,
    )

  @classmethod
  async def show_full_card_url(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a full card URL to the chat.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with card URL
    Returns:
      A dict with message encoded into bytes
    """
    card_uri = await ScryfallFetcher.get_card_url(card_name=message_text)
    if card_uri == "ambiguous":
      return Backend.ambiguous_card(
          chat_id=chat_id,
      )
    elif card_uri == "not_found":
      return Backend.card_not_found(
          card_name=message_text,
          chat_id=chat_id,
      )
    else:
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=card_uri,
          options={"disable_preview": False},
      )

  @classmethod
  async def show_card_image(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a card Image to the chat.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with card image URL
    Returns:
      A dict with message encoded into bytes
    """
    card_images = await ScryfallFetcher.get_card_image(card_name=message_text)
    if card_images == "ambiguous":
      return Backend.ambiguous_card(
          chat_id=chat_id,
      )
    elif card_images == "not_found":
      return Backend.card_not_found(
          card_name=message_text,
          chat_id=chat_id,
      )
    else:
      image_results = []
      for image in card_images:
        message =  Utils.generate_outgoing_message(
            command="image",
            chat_id=chat_id,
            message_text=image,
        )
        image_results.append(message)
      return image_results

  @classmethod
  async def show_quiz_image(
      cls,
      chat_id: str,
  ) -> bytes:
    """Sends a quiz card image URL to the chat.

    Args:
      chat_id: Id of the telegram chat to send message to
    Returns:
      A dict with message encoded into bytes
    """
    card_object = await ScryfallFetcher.get_card_image_art()
    if card_object:
      return Utils.generate_outgoing_message(
          command="quiz",
          chat_id=chat_id,
          message_text="",
          options=card_object,
      )
    else:
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text="Error generating a quiz. Please try again.",
      )

  @classmethod
  async def show_card_price(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a card prices to the chat.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with card name
    Returns:
      A dict with message encoded into bytes
    """
    card_prices = await ScryfallFetcher.get_card_prices(card_name=message_text)
    if card_prices == "ambiguous":
      return Backend.ambiguous_card(
          chat_id=chat_id,
      )
    elif card_prices == "not_found":
      return Backend.card_not_found(
          card_name=message_text,
          chat_id=chat_id,
      )
    else:
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=card_prices,
      )

  @classmethod
  async def handle_quiz_reply(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Resolves user reply to the quiz.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with the dict containing user answer data
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    text = message_dict.get("text", "")
    message_id = message_dict.get("message_id", "")
    user_card_name = "dummytext"
    if text:
      user_card_name = text.lower()
    # Check if the quiz with this message id exists
    quiz = await MongoClient.get_quiz_object(message_id=message_id)
    if quiz:
      quiz_card = quiz.get("card_name", "")
      quiz_card_name = quiz_card.lower()
      if len(user_card_name) < 5 and quiz_card_name == user_card_name or \
      len(user_card_name) >= 5 and user_card_name in quiz_card_name:
        card_url = await ScryfallFetcher.get_card_image(card_name=quiz_card)
        return Utils.generate_outgoing_message(
            command="image",
            chat_id=chat_id,
            message_text=card_url,
        )
    else:
      return Utils.generate_outgoing_message(
          command="void",
          chat_id=chat_id,
          message_text="void",
      )

  @classmethod
  async def show_help(
      cls,
      chat_id: str,
  ) -> bytes:
    """Sends a message with help info to the user.

    Args:
      chat_id: Id of the telegram chat to send message to
    Returns:
      A dict with message encoded into bytes
    """
    text = (
        "<b>Chat commands:</b>\n"
        "/c cardname - search for a card on scryfall\n"
        "/ci cardname - search for a card image on scryfall\n"
        "/cp cardname - search for a card price on scryfall\n"
        "/edhdanas - create a EDH danas poll or forward it if it exists\n"
        "<b>Account commands:</b>\n"
        "/reg - register you telegram account\n"
        "<b>Search commands:</b>\n"
        "/search - search in deckboxes & stores you're subscribed to\n"
        "/wish - search for cards from your deckbox wishlist"
        " in deckboxes & stores you're subscribed to\n"
        "<b>Menu commands:</b>\n"
        "/deckbox - opens a menu for manipulating your deckbox settings\n"
        "/conflux - opens a menu for manipulating your conflux settings\n"
        "/league - opens a menu for league play\n"
    )
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=text,
    )

  @classmethod
  async def show_deckbox_help(
      cls,
      chat_id: str,
  ) -> bytes:
    """Sends a message with help info to the user.

    Args:
      chat_id: Id of the telegram chat to send message to
    Returns:
      A dict with message encoded into bytes
    """
    text = (
        "/dbsearch - search for cards in specific deckboxes\n"
        "/dbwish - search for cards from your wishlist in specific deckboxes\n"
        "/regdeckbox - register you deckbox\n"
        "/updatedeckbox - updates you deckbox cache to be up-to-date\n"
        "/dbsub - subscribe to deckboxes\n"
        "/dbunsub - unsubscribe from deckboxes\n"
        "/mydeckbox - check your registered deckbox\n"
        "/mydeckboxsubs - show your current deckbox subscriptions\n"
        "/main - go back to the main menu\n"
    )
    return Utils.generate_outgoing_message(
        command="deckboxmenu",
        chat_id=chat_id,
        message_text=text,
    )

  @classmethod
  async def show_conflux_help(
      cls,
      chat_id: str,
  ) -> bytes:
    """Sends a message with conflux help info to the user.

    Args:
      chat_id: Id of the telegram chat to send message to
    Returns:
      A dict with message encoded into bytes
    """
    text = (
        "/consearch - search for cards in conflux\n"
        "/conwish - search for cards from your deckbox wishlist in confux\n"
        "/confluxsub - subscribe to see conflux in your regular searches\n"
        "/confluxunsub - unsubscribe from conflux in your regular searches\n"
        "/main - go back to the main menu\n"
    )
    return Utils.generate_outgoing_message(
        command="confluxmenu",
        chat_id=chat_id,
        message_text=text,
    )

  @classmethod
  async def show_league_help(
      cls,
      chat_id: str,
  ) -> bytes:
    """Sends a message with league help info to the user.

    Args:
      chat_id: Id of the telegram chat to send message to
    Returns:
      A dict with message encoded into bytes
    """
    text = (
        "/match - register a match in one of your leagues\n"
        "/mystandings - check your standings in one of your leagues\n"
        "/mymatches - check your match history for the league\n"
        "/leaguereg - register for a league (needs league ID and invite code)\n"
        "/leaderboards - check the leaderboards of your leagues\n"
        "/main - go back to the main menu\n"
    )
    return Utils.generate_outgoing_message(
        command="leaguemenu",
        chat_id=chat_id,
        message_text=text,
    )

  @classmethod
  async def edh_danas_send_poll(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a EDH dans poll to the chat or forwards the existing one.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with the dict containing EDH danas data
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    message = message_dict.get("message", "")
    options = message_dict.get("options")
    chat_type = message_dict.get("chat_type")
    now = datetime.now()
    datetime_string = now.strftime("%Y-%m-%d")
    existing = await MongoClient.check_edh_danas(timestamp=datetime_string)
    if existing:
      options = {
          "chat_id": existing.get("chat_id"),
          "message_id": existing.get("message_id"),
      }
      return Utils.generate_outgoing_message(
          command="forward",
          chat_id=chat_id,
          message_text="",
          options=options,
      )
    elif not existing and chat_type == "group":
      return Utils.generate_outgoing_message(
          command="poll",
          chat_id=chat_id,
          message_text=message,
          options=options,
      )
    elif not existing and chat_type == "private":
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text="No EDH Danas yet. Perhaps you shoud create it?",
      )

  @classmethod
  async def register_user(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Registers a user by adding them to the DB.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    if not message_text or message_text == "":
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"You need to have a telegram username!",
      )
    full_name = f"@{message_text}"
    new_user = {
        "telegram": full_name.lower(),
        "discord": "",
        "deckbox_name": "",
        "moxfield_name": "",
        "deckbox_subscriptions": {},
        "store_subscriptions": {},
        "chat_id": chat_id,
    }
    exists = await MongoClient.check_if_user_exists(telegram_name=full_name)
    if exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"The user {full_name} is already registered!",
      )
    else:
      success = await MongoClient.add_user(object=new_user)
      if not success:
        return Utils.generate_outgoing_message(
            command="menu",
            chat_id=chat_id,
            message_text=f"Failed to register user {full_name}! Try again!",
            options={"registered": success},
        )
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text="Successfully registered! Choose a command",
          options={"registered": success},
          )

  @classmethod
  async def get_user_menu(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a menu to the chat.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    if not message_text or message_text == "":
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"You need to have a telegram username!",
      )
    full_name = f"@{message_text}"
    text = "You need to register first! Use command /reg"
    exists = await MongoClient.check_if_user_exists(telegram_name=full_name)
    if exists:
      text = "Choose a command"
      # Check if user has chat ID assigned to them
      user_data = await MongoClient.get_user_data(
          telegram=full_name,
      )
      user_chat_id = user_data.get("chat_id")
      if not user_chat_id:
        update = await MongoClient.add_chat_id_to_user(
            chat_id=chat_id,
            telegram_name=full_name
        )
        if not update:
          print(f"Failed to add chat_id {chat_id} of user {full_name} to DB")
        else:
          text = "The bot can now send you updates!"
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=text,
        options={"registered": exists},
    )

  @classmethod
  async def get_deckbox_menu(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a decbkox menu to the chat.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    if not message_text or message_text == "":
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"You need to have a telegram username!",
      )
    full_name = f"@{message_text}"
    text = "You need to register first! Use command /reg"
    exists = await MongoClient.check_if_user_exists(telegram_name=full_name)
    if exists:
      text = "Choose a command"
    return Utils.generate_outgoing_message(
        command="deckboxmenu",
        chat_id=chat_id,
        message_text=text,
        options={"registered": exists},
    )

  @classmethod
  async def get_conflux_menu(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a conflux menu to the chat.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    if not message_text or message_text == "":
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"You need to have a telegram username!",
      )
    full_name = f"@{message_text}"
    text = "You need to register first! Use command /reg"
    exists = await MongoClient.check_if_user_exists(telegram_name=full_name)
    if exists:
      text = "Choose a command"
    return Utils.generate_outgoing_message(
        command="confluxmenu",
        chat_id=chat_id,
        message_text=text,
        options={"registered": exists},
    )

  @classmethod
  async def get_league_menu(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a league menu to the chat.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    if not message_text or message_text == "":
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"You need to have a telegram username!",
      )
    full_name = f"@{message_text}"
    text = "You need to register first! Use command /reg"
    exists = await MongoClient.check_if_user_exists(telegram_name=full_name)
    if exists:
      text = "Choose a command"
    return Utils.generate_outgoing_message(
        command="leaguemenu",
        chat_id=chat_id,
        message_text=text,
        options={"registered": exists},
    )

  @classmethod
  async def update_user_deckbox(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Updates user deckbox by re-caching it.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    telegram_name = f"@{message_text}"
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Get the username
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    username = user_data.get("deckbox_name")
    if not username:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"You don't have a registered deckbox yet.",
      )
    # Fetch deckbox lists IDs from the site
    ids = await Deckbox.get_deckbox_ids_from_account(account_name=username)
    if not ids.get("success"):
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"It appears the deckbox {username} doesn't exist",
      )
    tradelist_id = ids.get("tradelist")
    wishlist_id = ids.get("wishlist")
    # Update tradelist
    tradelist_result = await Backend.update_deckbox_cache_in_mongo(
        deckbox_id=tradelist_id,
        account_name=username,
        tradelist=True,
    )
    if not tradelist_result:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Failed to add tradelist. Try again.",
      )
    # Update wishlist
    wishlist_result = await Backend.update_deckbox_cache_in_mongo(
        deckbox_id=wishlist_id,
        account_name=username,
        wishlist=True,
    )
    if not wishlist_result:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Failed to add wishlist. Try again.",
      )
    return Utils.generate_outgoing_message(
        command="deckboxmenu",
        chat_id=chat_id,
        message_text="Your deckbox was updated.",
    )

  @classmethod
  async def add_deckbox_to_user(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Adds a deckbox to user in the DB.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict containing user name and deckbox name
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    deckbox = message_dict.get("deckbox", "")
    deckbox_lower = deckbox.lower()
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Check if deckbox already belongs to someone else
    existing_user = await MongoClient.get_user_data(deckbox=deckbox_lower)
    if existing_user and existing_user.get("telegram") != telegram_name:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Tradelist {deckbox} belongs to someone else!",
      )
    # Fetch deckbox lists IDs from the site
    ids = await Deckbox.get_deckbox_ids_from_account(account_name=deckbox)
    if not ids.get("success"):
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"It appears the deckbox {deckbox} doesn't exist",
      )
    tradelist_id = ids.get("tradelist")
    wishlist_id = ids.get("wishlist")
    # Add tradelist
    tradelist_result = await Backend.add_deckbox_to_mongo(
        deckbox_id=tradelist_id,
        account_name=deckbox,
        tradelist=True,
    )
    if not tradelist_result:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Failed to add tradelist. Try again.",
      )
    # Add wishlist
    wishlist_result = await Backend.add_deckbox_to_mongo(
        deckbox_id=wishlist_id,
        account_name=deckbox,
        wishlist=True,
    )
    if not wishlist_result:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Failed to add wishlist. Try again.",
      )
    (_, fin_msg) = await MongoClient.add_deckbox_to_user(
        deckbox=deckbox,
        telegram_name=telegram_name,
    )
    return Utils.generate_outgoing_message(
        command="deckboxmenu",
        chat_id=chat_id,
        message_text=fin_msg,
    )

  @classmethod
  async def add_subscription_to_user(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Adds a new subscription to the user in the DB.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and deckbox to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    deckbox = message_dict.get("deckbox")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Add a deckbox to mongo if it didn't exist
    ids = await Deckbox.get_deckbox_ids_from_account(account_name=deckbox)
    if not ids.get("success"):
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"It appears the deckbox {deckbox} doesn't exist",
      )
    tradelist_id = ids.get("tradelist")
    wishlist_id = ids.get("wishlist")
    # Add tradelist
    tradelist_result = await Backend.add_deckbox_to_mongo(
        deckbox_id=tradelist_id,
        account_name=deckbox,
        tradelist=True,
    )
    if not tradelist_result:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Failed to add tradelist. Try again.",
      )
    # Add wishlist
    wishlist_result = await Backend.add_deckbox_to_mongo(
        deckbox_id=wishlist_id,
        account_name=deckbox,
        wishlist=True,
    )
    if not wishlist_result:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Failed to add wishlist. Try again.",
      )
    result = await MongoClient.add_subscription_to_user(
        subscription_name=deckbox,
        telegram=telegram_name,
    )
    if not result:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Failed to subscribe to {deckbox}",
      )
    return Utils.generate_outgoing_message(
        command="deckboxmenu",
        chat_id=chat_id,
        message_text=f"You subscribed to {deckbox}",
    )

  @classmethod
  async def remove_subscription_from_user(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Removes a new subscription to the user in the DB.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and deckbox to remove
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    deckbox = message_dict.get("deckbox")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    result = await MongoClient.remove_subscription_from_user(
        subscription_name=deckbox,
        telegram=telegram_name,
    )
    if not result:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Failed to unsubscribe from {deckbox}",
      )
    return Utils.generate_outgoing_message(
        command="deckboxmenu",
        chat_id=chat_id,
        message_text=f"You unsubscribed from {deckbox}",
    )

  @classmethod
  async def check_user_deckbox(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Checks user's deckbox and sends them it's name.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    if not message_text or message_text == "":
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"You need to have a telegram username!",
      )
    full_name = f"@{message_text}"
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=full_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    current_user_data = await MongoClient.get_user_data(
        telegram=full_name,
    )
    current_deckbox = current_user_data.get("deckbox_name")
    if current_deckbox == "":
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"You haven't registered a deckbox yet!",
      )
    else:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"Your deckbox account name is: {current_deckbox}",
      )

  @classmethod
  async def check_user_deckbox_subscriptions(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Checks user's deckbox subscriptions and sends them to the user.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    if not message_text or message_text == "":
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"You need to have a telegram username!",
      )
    full_name = f"@{message_text}"
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=full_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="deckboxmenu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    subscriptions = await MongoClient.get_user_subscriptions(
        telegram=full_name,
    )
    final_string = "You are not subscribed to any deckboxes yet"
    if subscriptions:
        final_string = ""
        for sub in subscriptions.keys():
          final_string += f"{sub}\n"
    return Utils.generate_outgoing_message(
        command="deckboxmenu",
        chat_id=chat_id,
        message_text=final_string,
    )

  @classmethod
  async def bulk_search_cards(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Searches for cards in user subscriptions.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict containing user name and cards to search for
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    received_cards = message_dict.get("cards")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Check if user is subscrbed to deckboxes
    sub_dict = await MongoClient.get_user_subscriptions(
        telegram=telegram_name,
    )
    if not sub_dict:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You are not subscribed to any deckboxes!",
      )
    all_dicts = []
    if len(received_cards) > 10:
      cards_chunks = await Utils.split_list_into_chunks(
          input_list=received_cards,
          max_length=10,
      )
      for chunk in cards_chunks:
        chunk_result = await Backend.search_for_cards(
            received_cards=chunk,
            telegram_name=telegram_name,
        )
        all_dicts.append(chunk_result)
    else:
      search_result = await Backend.search_for_cards(
          received_cards=received_cards,
          telegram_name=telegram_name,
        )
      all_dicts.append(search_result)
    result = await Utils.construct_united_search_dict(input_dicts=all_dicts)
    sub_dict = await MongoClient.get_user_subscriptions(telegram=telegram_name)
    sub_list = list(sub_dict.keys())
    deckboxes = await MongoClient.match_deckbox_tradelist_ids_to_names(
        deckbox_names=sub_list,
    )
    messages = await Utils.construct_found_message(
        found_object=result,
        deckbox_names=deckboxes,
    )
    results = []
    for message in messages:
      part = Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=message,
      )
      results.append(part)
    return results

  @classmethod
  async def deckboxes_search_cards(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Searches for cards in selected deckboxes.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict containing user name and cards to search for
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    received_cards = message_dict.get("cards")
    received_deckboxes = message_dict.get("deckboxes")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Check if some of the requested deckboxes don't exist and add them
    all_dbs = await MongoClient.get_all_deckboxes(tradelist=True)
    for deckbox in received_deckboxes:
      if deckbox not in all_dbs:
        # Add a deckbox to mongo if it didn't exist
        ids = await Deckbox.get_deckbox_ids_from_account(account_name=deckbox)
        if not ids.get("success"):
          return Utils.generate_outgoing_message(
              command="deckboxmenu",
              chat_id=chat_id,
              message_text=f"It appears the deckbox {deckbox} doesn't exist",
          )
        tradelist_id = ids.get("tradelist")
        wishlist_id = ids.get("wishlist")
        # Add tradelist
        tradelist_result = await Backend.add_deckbox_to_mongo(
            deckbox_id=tradelist_id,
            account_name=deckbox,
            tradelist=True,
        )
        if not tradelist_result:
          return Utils.generate_outgoing_message(
              command="deckboxmenu",
              chat_id=chat_id,
              message_text=f"Failed to add tradelist. Try again.",
          )
        # Add wishlist
        wishlist_result = await Backend.add_deckbox_to_mongo(
            deckbox_id=wishlist_id,
            account_name=deckbox,
            wishlist=True,
        )
        if not wishlist_result:
          return Utils.generate_outgoing_message(
              command="deckboxmenu",
              chat_id=chat_id,
              message_text=f"Failed to add wishlist. Try again.",
          )
    all_dicts = []
    if len(received_cards) > 10:
      cards_chunks = await Utils.split_list_into_chunks(
          input_list=received_cards,
          max_length=10,
      )
      for chunk in cards_chunks:
        chunk_result = await Backend.search_for_cards(
            received_cards=chunk,
            telegram_name=telegram_name,
            received_deckboxes=received_deckboxes,
        )
        all_dicts.append(chunk_result)
    else:
      search_result = await Backend.search_for_cards(
          received_cards=received_cards,
          telegram_name=telegram_name,
          received_deckboxes=received_deckboxes,
        )
      all_dicts.append(search_result)
    result = await Utils.construct_united_search_dict(input_dicts=all_dicts)
    deckboxes = await MongoClient.get_all_deckboxes(tradelist=True)
    messages = await Utils.construct_found_message(
        found_object=result,
        deckbox_names=deckboxes,
    )
    results = []
    for message in messages:
      part = Utils.generate_outgoing_message(
        command="deckboxmenu",
        chat_id=chat_id,
        message_text=message,
      )
      results.append(part)
    return results

  @classmethod
  async def conflux_search_cards(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Searches for cards in conflux.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict containing user name and cards to search for
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    received_cards = message_dict.get("cards")
    search_type = message_dict.get("search")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    search_result = await Backend.search_for_cards_in_conflux(
        received_cards=received_cards,
    )
    messages = await Utils.construct_found_store_message(
        found_object=search_result,
        store_name="Conflux",
    )
    results = []
    command = "menu"
    match search_type:
      case "all":
        command = "menu"
      case "conflux":
        command = "confluxmenu"
      case _:
        command = "menu"
    for message in messages:
      part = Utils.generate_outgoing_message(
        command=command,
        chat_id=chat_id,
        message_text=message,
      )
      results.append(part)
    return results

  @classmethod
  async def search_cards_from_wishlist(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Searches for cards from user wishlist in user subscriptions.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    search_type = message_dict.get("search")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Check if user has a deckbox
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    user_deckbox = user_data.get("deckbox_name")
    if not user_deckbox:
      message = (
          "You need to register a deckbox first to get your wishlist!\n"
          "Use /regdeckbox to register a deckbox."
      )
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=message,
          options={"registered": True},
      )
    # Check if user is subscrbed to deckboxes
    sub_dict = await MongoClient.get_user_subscriptions(
        telegram=telegram_name,
    )
    if not sub_dict:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You are not subscribed to any deckboxes!",
      )
    # Find user's wishlist
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    deckbox = user_data.get("deckbox_name")
    wishlist_id = await MongoClient.get_deckbox_id(
        deckbox_name=deckbox,
        wishlist=True,
    )
    wishlist_cards_dict = await MongoClient.get_deckbox_cards_dict(
        deckbox_id=wishlist_id,
        wishlist=True,
    )
    wishlist_cards_list = list(wishlist_cards_dict.keys())
    wish_results = []
    if len(wishlist_cards_list) > 10:
      cards_chunks = await Utils.split_list_into_chunks(
          input_list=wishlist_cards_list,
          max_length=10,
      )
      for chunk in cards_chunks:
        chunk_result = await Backend.wish_for_cards(
            received_cards=chunk,
            telegram_name=telegram_name,
        )
        wish_results.append(chunk_result)
    else:
      result = await Backend.wish_for_cards(
          received_cards=wishlist_cards_list,
          telegram_name=telegram_name,
      )
      wish_results.append(result)
    sub_dict = await MongoClient.get_user_subscriptions(telegram=telegram_name)
    sub_list = list(sub_dict.keys())
    deckboxes = await MongoClient.match_deckbox_tradelist_ids_to_names(
        deckbox_names=sub_list,
    )
    total = await Utils.construct_united_search_dict(input_dicts=wish_results)
    messages = await Utils.construct_found_message(
        found_object=total,
        deckbox_names=deckboxes,
    )
    final_message_results = []
    command = "menu"
    match search_type:
      case "all":
        command = "menu"
      case "conflux":
        command = "confluxmenu"
      case _:
        command = "menu"
    for message in messages:
      part = Utils.generate_outgoing_message(
        command=command,
        chat_id=chat_id,
        message_text=message,
      )
      final_message_results.append(part)
    return final_message_results

  @classmethod
  async def deckboxes_search_cards_from_wishlist(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Searches for cards from user wishlist in user subscriptions.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    search_type = message_dict.get("search")
    received_deckboxes = message_dict.get("deckboxes")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Check if user has a deckbox
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    user_deckbox = user_data.get("deckbox_name")
    if not user_deckbox:
      message = (
          "You need to register a deckbox first to get your wishlist!\n"
          "Use /regdeckbox to register a deckbox."
      )
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=message,
          options={"registered": True},
      )
    # Find user's wishlist
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    deckbox = user_data.get("deckbox_name")
    wishlist_id = await MongoClient.get_deckbox_id(
        deckbox_name=deckbox,
        wishlist=True,
    )
    wishlist_cards_dict = await MongoClient.get_deckbox_cards_dict(
        deckbox_id=wishlist_id,
        wishlist=True,
    )
    wishlist_cards_list = list(wishlist_cards_dict.keys())
    wish_results = []
    if len(wishlist_cards_list) > 10:
      cards_chunks = await Utils.split_list_into_chunks(
          input_list=wishlist_cards_list,
          max_length=10,
      )
      for chunk in cards_chunks:
        chunk_result = await Backend.wish_for_cards(
            received_cards=chunk,
            telegram_name=telegram_name,
            received_deckboxes=received_deckboxes,
        )
        wish_results.append(chunk_result)
    else:
      result = await Backend.wish_for_cards(
          received_cards=wishlist_cards_list,
          telegram_name=telegram_name,
          received_deckboxes=received_deckboxes,
      )
      wish_results.append(result)
    deckboxes = await MongoClient.get_all_deckboxes(tradelist=True)
    total = await Utils.construct_united_search_dict(input_dicts=wish_results)
    messages = await Utils.construct_found_message(
        found_object=total,
        deckbox_names=deckboxes,
    )
    final_message_results = []
    command = "menu"
    match search_type:
      case "all":
        command = "menu"
      case "conflux":
        command = "confluxmenu"
      case "deckbox":
        command= "deckboxmenu"
      case _:
        command = "menu"
    for message in messages:
      part = Utils.generate_outgoing_message(
        command=command,
        chat_id=chat_id,
        message_text=message,
      )
      final_message_results.append(part)
    return final_message_results

  @classmethod
  async def conflux_search_wishlist(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Searches for cards from user wishlist in conflux.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    telegram_name = f"@{message_text}"
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Check if user has a deckbox
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    user_deckbox = user_data.get("deckbox_name")
    if not user_deckbox:
      message = (
          "You need to register a deckbox first to get your wishlist!\n"
          "Use /regdeckbox to register a deckbox."
      )
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=message,
          options={"registered": True},
      )
    # Find user's wishlist
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    deckbox = user_data.get("deckbox_name")
    wishlist_id = await MongoClient.get_deckbox_id(
        deckbox_name=deckbox,
        wishlist=True,
    )
    if not wishlist_id:
      return Utils.generate_outgoing_message(
          command="confluxmenu",
          chat_id=chat_id,
          message_text=f"You do not have a deckbox wishlist registered.",
          options={"registered": True},
      )
    wishlist_cards_dict = await MongoClient.get_deckbox_cards_dict(
        deckbox_id=wishlist_id,
        wishlist=True,
    )
    wishlist_cards_list = list(wishlist_cards_dict.keys())
    result = await Backend.wish_for_cards_in_conflux(
        received_cards=wishlist_cards_list,
    )
    messages = await Utils.construct_found_store_message(
        found_object=result,
        store_name="Conflux",
    )
    final_message_results = []
    for message in messages:
      part = Utils.generate_outgoing_message(
        command="confluxmenu",
        chat_id=chat_id,
        message_text=message,
      )
      final_message_results.append(part)
    return final_message_results

  @classmethod
  async def add_store(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Adds a new store to the DB.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with user name
    Returns:
      A dict with message encoded into bytes
    """
    name = message_text.lower()
    new_store = {
        "name": name,
        "cards": {},
    }
    exists = await MongoClient.check_if_store_exists(store_name=name)
    if exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"The store {name} is already registered!",
      )
    success = await MongoClient.add_store(object=new_store)
    if not success:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"Failed to add store {name}! Try again!",
          options={"registered": success},
      )
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=f"Successfully added store {name}!",
        options={"registered": success},
        )

  @classmethod
  async def add_store_subscription_to_user(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Adds a new subscription to the user in the DB.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    store = message_dict.get("store")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Check if the store exists in mongo db
    store_exists = await MongoClient.check_if_store_exists(
        store_name=store,
    )
    if not store_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"Store '{store}' not found!",
          options={"registered": True},
      )
    # Add store subscription to user
    result = await MongoClient.add_store_subscription_to_user(
        subscription_name=store,
        telegram=telegram_name,
    )
    if not result:
      return Utils.generate_outgoing_message(
          command="confluxmenu",
          chat_id=chat_id,
          message_text=f"Failed to subscribe to {store}",
      )
    return Utils.generate_outgoing_message(
        command="confluxmenu",
        chat_id=chat_id,
        message_text=f"You subscribed to {store}",
    )

  @classmethod
  async def remove_store_subscription_from_user(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Removes a store subscription to the user in the DB.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to remove
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    store = message_dict.get("store")
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="confluxmenu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    result = await MongoClient.remove_store_subscription_from_user(
        subscription_name=store,
        telegram=telegram_name,
    )
    if not result:
      return Utils.generate_outgoing_message(
          command="confluxmenu",
          chat_id=chat_id,
          message_text=f"Failed to unsubscribe from {store}",
      )
    return Utils.generate_outgoing_message(
        command="confluxmenu",
        chat_id=chat_id,
        message_text=f"You unsubscribed from {store}",
    )

  @classmethod
  async def recache_deckboxes_manually(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Re-caches all deckboxes in the DB manually.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and deckbox to add
    Returns:
      A dict with message encoded into bytes
    """
    await Backend.deckboxes_cache_scheduled_job()
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=f"Completed manual deckboxes re-cache",
    )

  @classmethod
  async def update_leagues_manually(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Updates all leagues in the DB manually.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and deckbox to add
    Returns:
      A dict with message encoded into bytes
    """
    await Backend.league_new_week_scheduled_job()
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=f"Completed manual leagues update",
    )

  @classmethod
  async def recache_conflux_manually(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Re-caches conflux store in the DB manually.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and deckbox to add
    Returns:
      A dict with message encoded into bytes
    """
    await Backend.conflux_cache_scheduled_job()
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=f"Completed manual conflux caching!",
    )

  @classmethod
  async def create_league(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Adds a new league to DB and sends back it's ID.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    league_name = message_dict.get("league_name")
    league_length = message_dict.get("league_length")
    league_id = await Utils.generate_random_id(length=5)
    # Check if the ID is duplicated
    league_exists = await MongoClient.get_league(league_id=league_id)
    while league_exists:
      league_id = await Utils.generate_random_id(length=5)
      league_exists = await MongoClient.get_league(league_id=league_id)
    result = await League.create_league(
        league_id=league_id,
        league_name=league_name,
        league_length=league_length,
    )
    if not result:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"Failed to create a league",
      )
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=f"{league_id}",
    )

  @classmethod
  async def subscribe_to_league(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Subscribes a channel to league updates.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    league_id = message_dict.get("league_id")
    sub_chat_id = message_dict.get("chat_id")
    # Get the league name
    league = await MongoClient.get_league(league_id=league_id)
    league_name = league.get("league_name")
    add_result = await MongoClient.add_league_subscription(
        chat_id=sub_chat_id,
        league_id=league_id,
    )
    if not add_result:
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"Failed to add subscription to {league_name}",
      )
    return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"This channed is subscribed to {league_name}",
      )

  @classmethod
  async def unsubscribe_from_league(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Ubsubscribes a channel from league updates.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    league_id = message_dict.get("league_id")
    sub_chat_id = message_dict.get("chat_id")
    # Get the league name
    league = await MongoClient.get_league(league_id=league_id)
    league_name = league.get("league_name")
    add_result = await MongoClient.remove_league_subscription(
        chat_id=sub_chat_id,
        league_id=league_id,
    )
    if not add_result:
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"Failed to remove subscription to {league_name}",
      )
    return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"This channed is unsubscribed from {league_name}",
      )

  @classmethod
  async def change_league_status(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Changes the status of the league to active/unactive.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    league_id = message_dict.get("league_id")
    status = message_dict.get("status")
    # Get the league name
    league = await MongoClient.get_league(league_id=league_id)
    league_name = league.get("league_name")
    update_result = await MongoClient.change_league_status(
        status=status,
        league_id=league_id,
    )
    if not update_result:
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"Failed to update status of {league_name}",
      )
    return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=f"{league_name} status set to: {status}",
      )

  @classmethod
  async def create_league_invite(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Adds a new league invite to DB and sends back it's ID.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    league_id = message_text
    invite_id = await Utils.generate_random_id(length=10)
    # Check if league exists
    league_exists = await MongoClient.get_league(league_id=league_id)
    if not league_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"The league with ID {league_id} doesn't exist!",
      )
    result = await League.create_league_invite(
        league_id=league_id,
        invite_id=invite_id,
    )
    if not result:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"Failed to create an invite",
      )
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=f"{invite_id}",
    )

  @classmethod
  async def create_league_player(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Adds a new player to league.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    telegram = message_dict.get("telegram")
    chat_id = message_dict.get("chat_id")
    league_id = message_dict.get("league_id")
    league_user = message_dict.get("league_user")
    # Get the league name
    league = await MongoClient.get_league(league_id=league_id)
    if not league:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"League ID {league_id} doesn't exist",
      )
    league_name = league.get("league_name")
    # Get the user leagues and see if they are already registered
    player_data = await MongoClient.check_if_player_in_league(
        telegram=telegram,
        league_id=league_id,
    )
    if player_data:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"You are already registered in '{league_name}!",
      )
    # Check if league invite exists
    invite_exists = await MongoClient.get_league_invite(invite_code=league_user)
    if not invite_exists:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"The invite code {league_user} doesn't exist!",
      )
    delete_result = await MongoClient.delete_league_invite(
        invite_id=league_user,
    )
    if not delete_result:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"Failed to process the invite",
      )
    result = await League.create_league_player(
        telegram=telegram,
        chat_id=chat_id,
        league_id=league_id,
    )
    if not result:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"Failed to register a league player",
      )
    return Utils.generate_outgoing_message(
        command="leaguemenu",
        chat_id=chat_id,
        message_text=f"You're registered for the league '{league_name}'!",
    )

  @classmethod
  async def send_match_result(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Sends a match confirmation to a player.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    print("MESSAGE DICT\n")
    print(message_dict)
    league_id = message_dict.get("league_id")
    player_sender = message_dict.get("player_one")
    player_receiver = message_dict.get("player_two")
    match_result = message_dict.get("result")
    league = await MongoClient.get_league(league_id=league_id)
    league_name = league.get("league_name", "")
    receiving_user = await MongoClient.get_league_player(
        telegram=player_receiver,
        league_id=league_id,
    )
    receiving_chat_id = receiving_user.get("chat_id")
    message = (
        f"{league_id}%{player_sender}%{match_result}%{player_receiver}\n"
        f"{player_sender} has registered a match result for: \n"
        f"{league_name} \n"
        f"{player_sender} {match_result} {player_receiver}\n"
        "Is this correct?\n"
    )
    return Utils.generate_outgoing_message(
        command="leaguematchconfirm",
        chat_id=receiving_chat_id,
        message_text=message,
    )

  @classmethod
  async def confirm_match_result(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Confirms a match result.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    league_id = message_dict.get("league_id")
    player_one = message_dict.get("player_one")
    player_two = message_dict.get("player_two")
    match_result = message_dict.get("result")
    league = await MongoClient.get_league(league_id=league_id)
    player_one_data = await MongoClient.get_league_player(
        telegram=player_one,
        league_id=league_id,
    )
    player_two_data = await MongoClient.get_league_player(
        telegram=player_two,
        league_id=league_id,
    )
    # Check the total amount of standings against the same person allowed now
    standings_total = league.get("current_week") * 3
    print(f"TOTAL STANDING MATCHES: {standings_total}")
    standings_same_player = league.get("current_week")
    print(f"STANDINGS AGAINST SAME PLAYER ALLOWED: {standings_same_player}")
    # Bools for determining if it is the standing match for players
    player_one_standing_played = player_one_data.get("standing_matches_played")
    player_two_standing_played = player_two_data.get("standing_matches_played")
    player_one_standing = False
    player_two_standing = False
    # Check the amount of standing games player one has against player two
    standing_player_1_vs = await MongoClient.get_player_standing_against_player(
        player_one=player_one,
        player_two=player_two,
    )
    standings_p1_vs_p2 = len(standing_player_1_vs)
    print(f"Total standings P1 has against P2: {standings_p1_vs_p2}")
    # Check the amount of standing games player two has against player one
    standing_player_2_vs = await MongoClient.get_player_standing_against_player(
        player_one=player_two,
        player_two=player_one,
    )
    standings_p2_vs_p1 = len(standing_player_2_vs)
    print(f"Total standings P2 has against P1: {standings_p2_vs_p1}")
    # Allow standing for player one
    if (player_one_standing_played < standings_total 
        and
        standings_p1_vs_p2 < standings_same_player 
        ):
      player_one_standing = True
    # Allow standing for player two
    if (player_two_standing_played < standings_total 
        and
        standings_p2_vs_p1 < standings_same_player 
        ):
      player_two_standing = True
    # Add a match to the DB
    match_added = await League.create_league_match(
        player_one=player_one,
        player_two=player_two,
        result=match_result,
        league_id=league_id,
        player_one_standing=player_one_standing,
        player_two_standing=player_two_standing,
    )
    if not match_added:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"Couldn't add a match to the DB, please try again!",
      )
    # Update player scores
    player_one_streak = player_one_data.get("win_streak")
    player_two_streak = player_two_data.get("win_streak")
    results = match_result.split("-")
    player_one_score = int(results[0])
    player_two_score = int(results[1])
    # Player 1 broke streak
    if player_two_streak > 2 and player_one_score > player_two_score:
      message = (
          f"{player_one} broke {player_two}'s "
          f"{player_two_streak} matches win streak!"
      )
      await League.league_broadcast_message(
          league_id=league_id,
          message=message,
      )
    # Player 2 broke streak
    if player_one_streak > 2 and player_two_score > player_one_score:
      message = (
          f"{player_two} broke {player_one}'s "
          f"{player_one_streak} matches win streak!"
      )
      await League.league_broadcast_message(
          league_id=league_id,
          message=message,
      )
    update_p1 = await MongoClient.update_player(
        telegram=player_one,
        win=player_one_score > player_two_score,
        standing=player_one_standing,
        broke_streak=player_two_streak > 2,
    )
    if not update_p1:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"Couldn't update player data, please contact admin!",
      )
    update_p2 = await MongoClient.update_player(
        telegram=player_two,
        win=player_one_score < player_two_score,
        standing=player_two_standing,
        broke_streak=player_one_streak > 2,
    )
    if not update_p2:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"Couldn't update player data, please contact admin!",
      )
    return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"Your match has been recorded!",
      )

  @classmethod
  async def check_league_standings(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Checks player's standings in a league.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    league_id = message_dict.get("league_id")
    telegram = message_dict.get("telegram")
    league = await MongoClient.get_league(league_id=league_id)
    player_data = await MongoClient.get_league_player(
        telegram=telegram,
        league_id=league_id,
    )
    if not player_data:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"User {telegram} is not in that league!",
      )
    all_players = await MongoClient.get_all_leagues_players(league_id=league_id)
    league_name = league.get("league_name")
    league_weeks_total = league.get("total_duration_weeks")
    league_current_week = league.get("current_week")
    date_joined = player_data.get("date_joined")
    total_points = player_data.get("total_points")
    standing_matches_ = player_data.get("standing_matches_played")
    standing_wins = player_data.get("standing_wins")
    standing_losses = player_data.get("standing_losses")
    total_played = player_data.get("total_played")
    total_wins = player_data.get("total_wins")
    total_losses = player_data.get("total_losses")
    win_streak = player_data.get("win_streak")
    total_standing = int(league_current_week) * 3
    resulting_message = (
        f"<b>{league_name}</b>\n"
        f"Current week: {league_current_week}/{league_weeks_total}\n"
        f"You joined: {date_joined}\n"
        f"Your total points: {total_points}\n"
        f"Total matches played: {total_played}\n"
        f"Total score: {total_wins}-{total_losses}\n"
        f"Standings matches played: {standing_matches_}/{total_standing}\n"
        f"Standings score: {standing_wins}-{standing_losses}\n"
        f"Your current win streak: {win_streak}\n\n"
    )
    return Utils.generate_outgoing_message(
        command="leaguemenu",
        chat_id=chat_id,
        message_text=resulting_message,
    )

  @classmethod
  async def check_league_stats(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Checks a league status and leaderboard.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    league_id = message_dict.get("league_id")
    telegram = message_dict.get("telegram")
    league = await MongoClient.get_league(league_id=league_id)
    player_data = await MongoClient.get_league_player(
        telegram=telegram,
        league_id=league_id,
    )
    if not player_data:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=f"User {telegram} is not in that league!",
      )
    all_players = await MongoClient.get_all_leagues_players(league_id=league_id)
    # Get the leaderboard
    sorted_players = sorted(
      all_players,
      key=lambda x: x["total_points"],
      reverse=True,
    )
    top_players = []
    for player in sorted_players[:10]:
      streak = ""
      if player["win_streak"] >=3:
        streak = f"🔥"
      player_message = (
          f"{player["telegram"]} "
          f"{player["standing_wins"]}-{player["standing_losses"]} "
          f"({player["total_points"]} points) {streak}"
      )
      top_players.append(player_message)
    leaderboard_players = "\n".join(top_players)
    leaderboard = "\n<b>Top 10 players:</b>\n" + leaderboard_players
    player_count = len(all_players)
    league_name = league.get("league_name")
    league_weeks_total = league.get("total_duration_weeks")
    league_current_week = league.get("current_week")
    resulting_message = (
        f"<b>{league_name}</b>\n"
        f"Total players: {player_count}\n"
        f"Current week: {league_current_week}/{league_weeks_total}\n"
        f"{leaderboard}"
    )
    return Utils.generate_outgoing_message(
        command="leaguemenu",
        chat_id=chat_id,
        message_text=resulting_message,
    )

  @classmethod
  async def check_match_stats(
      cls,
      chat_id: str,
      message_text: str,
  ) -> bytes:
    """Checks user's matches for a league.

    Args:
      chat_id: Id of the telegram chat to send message to
      message_text: text with dict with user name and store to add
    Returns:
      A dict with message encoded into bytes
    """
    message_dict = json.loads(message_text)
    league_id = message_dict.get("league_id")
    telegram = message_dict.get("telegram")
    league = await MongoClient.get_league(league_id=league_id)
    league_name = league.get("league_name")
    matches = await MongoClient.get_all_player_matches(telegram=telegram)
    if not matches:
      return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text="You have not played any matches yet!",
      )
    sorted_standing_matches = sorted(
    (match for match in matches if match["standings"].get(telegram) is True),
    key=lambda x: datetime.strptime(x["date_played"], "%d.%m.%Y %H:%M")
    )
    result_message = (
        f"<b>{league_name}</b>\n"
        "<b>Your standing matches:</b>\n"
    )
    standing_messages = []
    for match in sorted_standing_matches:
      if match["player_one"] == telegram:
        result = match["result"]
        message = f"{match["player_one"]} {result} {match["player_two"]}"
      elif match["player_two"] == telegram:
        result = match["result"][::-1]
        message = f"{match["player_two"]} {result} {match["player_one"]}"
      standing_messages.append(message)
    standing_message = "\n".join(standing_messages)
    result_message += standing_message
    sorted_tiebreaker_matches = sorted(
    (match for match in matches if match["standings"].get(telegram) is False),
    key=lambda x: datetime.strptime(x["date_played"], "%d.%m.%Y %H:%M")
    )
    if sorted_tiebreaker_matches:
      result_message += "\n<b>Your tiebreaker matches:</b>\n"
      tie_messages = []
      for match in sorted_tiebreaker_matches:
        if match["player_one"] == telegram:
          result = match["result"]
          message = f"{match["player_one"]} {result} {match["player_two"]}"
        elif match["player_two"] == telegram:
          result = match["result"][::-1]
          message = f"{match["player_two"]} {result} {match["player_one"]}"
        tie_messages.append(message)
      tie_message = "\n".join(tie_messages)
      result_message += tie_message
    return Utils.generate_outgoing_message(
          command="leaguemenu",
          chat_id=chat_id,
          message_text=result_message,
      )

  @classmethod
  async def resolve_command(
      cls,
      chat_id: str,
      command: str,
      message_text: str,
  ) -> bytes:
    """Resolves a command that came in the queue.

    Args:
      chat_id: Id of the telegram chat to send message to
      command: received command
      message_text: text that will be send to the command function
    Returns:
      A dict with message encoded into bytes
    """
    match command:
      case "any_message" | "help":
        return await cls.show_help(chat_id=chat_id)
      case "dbhelp":
        return await cls.show_deckbox_help(chat_id=chat_id)
      case "confluxhelp":
        return await cls.show_conflux_help(chat_id=chat_id)
      case "leaguehelp":
        return await cls.show_league_help(chat_id=chat_id)
      # Scryfall card URL fetcher
      case "c":
        return await cls.show_full_card_url(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Scryfall card image fetcher
      case "ci":
        return await cls.show_card_image(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Scryfall card price fetcher
      case "cp":
        return await cls.show_card_price(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Sending a message to user
      case "sendmsg":
        return await cls.send_freeform_message(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Registering a user
      case "reg":
        return await cls.register_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Registering a deckbox for a user
      case "regdeckbox":
        return await cls.add_deckbox_to_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Checking current registered deckbox
      case "mydeckbox":
        return await cls.check_user_deckbox(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Updating users deckbox
      case "updatedeckbox":
        return await cls.update_user_deckbox(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Adding a subscription to user
      case "dbsub":
        return await cls.add_subscription_to_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Removing a subscription from user
      case "dbunsub":
        return await cls.remove_subscription_from_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Checking user subscriptions
      case "mydeckboxsubs":
        return await cls.check_user_deckbox_subscriptions(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Searching for chosen cards
      case "search":
        return await cls.bulk_search_cards(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Searching for chosen cards in chosen deckboxes
      case "dbsearch":
        return await cls.deckboxes_search_cards(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Searching for cards from a wishlist
      case "wish":
        return await cls.search_cards_from_wishlist(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Searching for cards from a wishlist in chosen deckboxes
      case "dbwish":
        return await cls.deckboxes_search_cards_from_wishlist(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Sending a starting menu
      case "start":
        return await cls.get_user_menu(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Sending a deckbox menu
      case "deckboxmenu":
        return await cls.get_deckbox_menu(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Sending a conflux menu
      case "confluxmenu":
        return await cls.get_conflux_menu(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Sending a league menu
      case "leaguemenu":
        return await cls.get_league_menu(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Creating/forwarding a EDH danas poll
      case "edhdanas":
        return await cls.edh_danas_send_poll(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Sending a new quiz message
      case "quiz":
        return await cls.show_quiz_image(
            chat_id=chat_id,
        )
      # Handling quiz replies
      case "quiz_answer":
        return await cls.handle_quiz_reply(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Handling quiz replies
      case "addstore":
        return await cls.add_store(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Subscribing to conflux
      case "confluxsub":
        return await cls.add_store_subscription_to_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Unsubscribing from conflux
      case "confluxunsub":
        return await cls.remove_store_subscription_from_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Searching for cards in conflux
      case "consearch":
        return await cls.conflux_search_cards(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Searching for cards from a wishlist in conflux
      case "conwish":
        return await cls.conflux_search_wishlist(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Re-caching all deckboxes manually
      case "deckboxrecache":
        return await cls.recache_deckboxes_manually(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Re-caching conflux manually
      case "confluxcache":
        return await cls.recache_conflux_manually(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Subscribing channel to a league
      case "league_subscribe":
        return await cls.subscribe_to_league(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Unsubscribing channel from a league
      case "league_unsubscribe":
        return await cls.unsubscribe_from_league(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Activating/Deactivating a league
      case "league_status_change":
        return await cls.change_league_status(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Creating a new league
      case "league_create":
        return await cls.create_league(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "league_invite":
        return await cls.create_league_invite(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "league_user_reg":
        return await cls.create_league_player(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "league_match_result_send":
        return await cls.send_match_result(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "league_match_result_confirm":
        return await cls.confirm_match_result(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "league_standings_check":
        return await cls.check_league_standings(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "league_stats_check":
        return await cls.check_league_stats(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "league_matches_check":
        return await cls.check_match_stats(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Updating leagues manually
      case "leagues_update":
        return await cls.update_leagues_manually(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Any unknown commands
      case _:
        text = f"Unkown command: {command}"
        return Utils.generate_outgoing_message(
            command="text",
            chat_id=chat_id,
            message_text=text,
        )
