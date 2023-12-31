"""Module for resolving commands sent by from-user-listener.
"""
import json
from bot.deckbox.deckbox import Deckbox
from bot.scryfall.scryfall import ScryfallFetcher
from bot.mongo.mongo_client import MongoClient
from bot.utils.utils import Utils
from bot.deckbox.deckbox import Deckbox
from bot.backend.backend import Backend
from datetime import datetime

class TelegramCommands:

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
        "<b>Deckbox commands:</b>\n"
        "/search - search for cards in deckboxes you're subscribed to\n"
        "/wish - search for cards from your deckbox wishlist"
        " in deckboxes you're subscribed to\n"
        "/regdeckbox - register you deckbox\n"
        "/updatedeckbox - updates you deckbox cache to be up-to-date\n"
        "/dbsub subscribe to deckboxes\n"
        "/dbunsub - unsubscribe from deckboxes\n"
        "/mydeckbox - check your registered deckbox\n"
        "/mydeckboxsubs - show your current deckbox tradelist subscriptions\n"
    )
    return Utils.generate_outgoing_message(
        command="menu",
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
    return Utils.generate_outgoing_message(
        command="menu",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Get the username
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    username = user_data.get("deckbox_name")
    if not username:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You don't have a registered deckbox yet.",
      )
    # Fetch deckbox lists IDs from the site
    ids = await Deckbox.get_deckbox_ids_from_account(account_name=username)
    if not ids.get("success"):
      return Utils.generate_outgoing_message(
          command="menu",
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
          command="menu",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"Failed to add wishlist. Try again.",
      )
    return Utils.generate_outgoing_message(
        command="menu",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Check if deckbox already belongs to someone else
    existing_user = await MongoClient.get_user_data(deckbox=deckbox_lower)
    if existing_user and existing_user.get("telegram") != telegram_name:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"Tradelist {deckbox} belongs to someone else!",
      )
    # Fetch deckbox lists IDs from the site
    ids = await Deckbox.get_deckbox_ids_from_account(account_name=deckbox)
    if not ids.get("success"):
      return Utils.generate_outgoing_message(
          command="menu",
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
          command="menu",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"Failed to add wishlist. Try again.",
      )
    (_, fin_msg) = await MongoClient.add_deckbox_to_user(
        deckbox=deckbox,
        telegram_name=telegram_name,
    )
    return Utils.generate_outgoing_message(
        command="menu",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    # Add a deckbox to mongo if it didn't exist
    ids = await Deckbox.get_deckbox_ids_from_account(account_name=deckbox)
    if not ids.get("success"):
      return Utils.generate_outgoing_message(
          command="menu",
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
          command="menu",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"Failed to add wishlist. Try again.",
      )
    result = await MongoClient.add_subscription_to_user(
        subscription_name=deckbox,
        telegram=telegram_name,
    )
    if not result:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"Failed to subscribe to {deckbox}",
      )
    return Utils.generate_outgoing_message(
        command="menu",
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
          command="menu",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"Failed to unsubscribe from {deckbox}",
      )
    return Utils.generate_outgoing_message(
        command="menu",
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
          command="menu",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"You haven't registered a deckbox yet!",
      )
    else:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"Your deckbox tradelist is: {current_deckbox}",
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
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          options={"registered": False},
      )
    subscriptions = await MongoClient.get_user_subscriptions(
        telegram=full_name,
    )
    final_string = "You are not subscribed to any deckboxes yet"
    if subscriptions:
        final_string = "You are subscribed to:\n"
        for sub in subscriptions.keys():
          final_string += f"{sub}\n"
    return Utils.generate_outgoing_message(
        command="menu",
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
    for message in messages:
      part = Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=message,
      )
      final_message_results.append(part)
    return final_message_results

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
      # Searching for cards from a wishlist
      case "wish":
        return await cls.search_cards_from_wishlist(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Sending a starting menu
      case "start":
        return await cls.get_user_menu(
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
      # Any unknown commands
      case _:
        text = f"Unkown command: {command}"
        return Utils.generate_outgoing_message(
            command="text",
            chat_id=chat_id,
            message_text=text,
        )
