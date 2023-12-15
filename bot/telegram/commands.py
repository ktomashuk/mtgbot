import json
from bot.deckbox.deckbox import Deckbox
from bot.scryfall.scryfall import ScryfallFetcher
from bot.mongo.mongo_client import MongoClient
from bot.utils.utils import Utils
from bot.deckbox.deckbox import Deckbox
from datetime import datetime

class TelegramCommands:

  @classmethod
  def card_not_found(
      cls,
      card_name: str,
      chat_id: str
  ):
    text = f"Card '{card_name}' not found!"
    return Utils.generate_outgoing_message(
            command="text",
            chat_id=chat_id,
            message_text=text,
        )

  @classmethod
  async def show_full_card_url(
      cls,
      chat_id: str,
      message_text: str,
  ):
    card_uri = await ScryfallFetcher.get_card_url(card_name=message_text)
    if card_uri:
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=card_uri,
          options={"disable_preview": False},
      )
    else:
      return cls.card_not_found(
          card_name=message_text,
          chat_id=chat_id,
      )

  @classmethod
  async def show_card_image(
      cls,
      chat_id: str,
      message_text: str,
  ):
    card_uri = await ScryfallFetcher.get_card_image(card_name=message_text)
    if card_uri:
      return Utils.generate_outgoing_message(
          command="image",
          chat_id=chat_id,
          message_text=card_uri,
      )
    else:
      return cls.card_not_found(
          card_name=message_text,
          chat_id=chat_id,
      )

  @classmethod
  async def show_card_price(
      cls,
      chat_id: str,
      message_text: str,
  ):
    card_prices = await ScryfallFetcher.get_card_prices(card_name=message_text)
    if card_prices:
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text=card_prices,
      )
    else:
      return cls.card_not_found(
          card_name=message_text,
          chat_id=chat_id,
      )

  @classmethod
  async def show_help(
      cls,
      chat_id: str,
  ):
    text = (
        "<b>Scryfall commands:</b>\n"
        "/c cardname - search for a card on scryfall\n"
        "/ci cardname - search for a card image on scryfall\n"
        "/cp cardname - search for a card price on scryfall\n"
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
  ):
    message_dict = json.loads(message_text)
    message = message_dict.get("message", "")
    options = message_dict.get("options")
    now = datetime.now()
    datetime_string = now.strftime("%Y-%m-%d %H:%M:%S")
    existing = await MongoClient.check_edh_danas()
    if existing:
      existing_date = existing.get("timestamp")
      check_if_older = Utils.check_if_next_day(
          current_day=datetime_string,
          previous_day=existing_date,
      )
      if check_if_older:
        print("FOUND DANAS AND IT'S OLDER")
      else:
        print("FOUND DANAS AND IT'S NEW")
      return Utils.generate_outgoing_message(
          command="text",
          chat_id=chat_id,
          message_text="FOUND",
      )
    else:
      print("CREATING NEW POLL")
      return Utils.generate_outgoing_message(
          command="poll",
          chat_id=chat_id,
          message_text=message,
          options=options,
      )

  @classmethod
  async def register_user(
      cls,
      chat_id: str,
      message_text: str,
  ):
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
            status=success,
        )
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text="Successfully registered! Choose a command",
          status=success,
      )

  @classmethod
  async def get_user_menu(
      cls,
      chat_id: str,
      message_text: str,
  ):
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
        status=exists,
    )

  @classmethod
  async def add_deckbox_to_mongo(
      cls,
      deckbox_id: str,
      account_name: str,
      tradelist: bool = False,
      wishlist: bool = False,
  ):
    # Check if the list already exists in mongo db
    list_exists = await MongoClient.check_if_deckbox_exists(
        deckbox_id=deckbox_id,
        tradelist=tradelist,
        wishlist=wishlist,
    )
    if list_exists:
      # Check if tradelist is already cached and cache is younger than 12 hours
      already_cached = await MongoClient.check_deckbox_cache(
          deckbox_id=deckbox_id,
          tradelist=tradelist,
          wishlist=wishlist,
      )
      if not already_cached:
        print("The tradelist is cached, but the cache is too old!")
        name = await MongoClient.get_deckbox_name(
            deckbox_id=deckbox_id,
            tradelist=tradelist,
            wishlist=wishlist,
        )
        new_cache = await Deckbox.cache_deckbox_list(
            deckbox=deckbox_id,
            account_name=name,
        )
        (new_status, _) = await MongoClient.update_deckbox(
            deckbox=deckbox_id,
            object=new_cache,
            tradelist=tradelist,
            wishlist=wishlist,
        )
        # If something went wrong when updating the tradelist
        if not new_status:
          return False
      return True
    # If tradelist doesn't exist yet
    else:
      new_cache = await Deckbox.cache_deckbox_list(
          deckbox=deckbox_id,
          account_name=account_name,
      )
      result = await MongoClient.add_deckbox(
          object=new_cache,
          tradelist=tradelist,
          wishlist=wishlist,
      )
      return result

  @classmethod
  async def update_deckbox_cache_in_mongo(
      cls,
      deckbox_id: str,
      account_name: str,
      tradelist: bool = False,
      wishlist: bool = False,
  ):
    # Check if the list already exists in mongo db
    list_exists = await MongoClient.check_if_deckbox_exists(
        deckbox_id=deckbox_id,
        tradelist=tradelist,
        wishlist=wishlist,
    )
    if list_exists:
      name = await MongoClient.get_deckbox_name(
          deckbox_id=deckbox_id,
          tradelist=tradelist,
          wishlist=wishlist,
      )
      new_cache = await Deckbox.cache_deckbox_list(
          deckbox=deckbox_id,
          account_name=name,
      )
      (new_status, _) = await MongoClient.update_deckbox(
          deckbox=deckbox_id,
          object=new_cache,
          tradelist=tradelist,
          wishlist=wishlist,
      )
      # If something went wrong when updating the tradelist
      if not new_status:
        return False
      return True
    # If tradelist doesn't exist yet
    else:
      new_cache = await Deckbox.cache_deckbox_list(
          deckbox=deckbox_id,
          account_name=account_name,
      )
      result = await MongoClient.add_deckbox(
          object=new_cache,
          tradelist=tradelist,
          wishlist=wishlist,
      )
      return result

  @classmethod
  async def update_user_deckbox(
      cls,
      chat_id: str,
      message_text: str,
  ):
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
          status=False,
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
    tradelist_result = await cls.update_deckbox_cache_in_mongo(
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
    wishlist_result = await cls.update_deckbox_cache_in_mongo(
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
  ):
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
          status=False,
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
    tradelist_result = await cls.add_deckbox_to_mongo(
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
    wishlist_result = await cls.add_deckbox_to_mongo(
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
    # Check if deckbox already belongs to someone else
    existing_user = await MongoClient.get_user_data(deckbox=deckbox)
    if existing_user and existing_user.get("telegram") != telegram_name:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"Tradelist {deckbox} belongs to someone else!",
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
  ):
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
          status=False,
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
    tradelist_result = await cls.add_deckbox_to_mongo(
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
    wishlist_result = await cls.add_deckbox_to_mongo(
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
  ):
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
          status=False,
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
  ):
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
          status=False,
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
  ):
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
          status=False,
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
  async def look_for_card_in_list(
      cls,
      card_name: str,
      card_list: list[str],
  ) -> list[str]:
    """Searches for a card name in a list of cards.

    Args:
      card_name: name of the card to search for
      card_list: list of cards to search in
    Returns:
      A list of cards that were found
    """
    card_name = card_name.replace("\u2019", "'")
    card_result = []
    first_letter = card_name[0]
    for card in card_list:
      if card_name in card:
        card_result.append(card)
      if not card_name.startswith(first_letter):
        break
    return card_result

  @classmethod
  async def bulk_search_cards(
      cls,
      chat_id: str,
      message_text: str,
  ):
    message_dict = json.loads(message_text)
    telegram_name = f"@{message_dict.get("telegram", "")}"
    received_cards = message_dict.get("cards")
    if len(received_cards) > 10:
      cards_chunks = await Utils.split_list_into_chunks(
          input_list=received_cards,
          max_length=10,
      )
      print(f"CARD CHUNKS: {cards_chunks}")
      results = []
      for chunk in cards_chunks:
        chunk_result = await cls.search_for_cards(
            chat_id=chat_id,
            received_cards=chunk,
            telegram_name=telegram_name,
        )
        results.append(chunk_result)
      return results
    else:
      result = await cls.search_for_cards(
          chat_id=chat_id,
          received_cards=received_cards,
          telegram_name=telegram_name,
      )
      return result

  @classmethod
  async def search_cards_from_wishlist(
      cls,
      chat_id: str,
      message_text: str,
  ):
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
          status=False,
      )
    # Find user's wishlist
    user_data = await MongoClient.get_user_data(telegram=telegram_name)
    deckbox = user_data.get("deckbox_name")
    ids = await Deckbox.get_deckbox_ids_from_account(account_name=deckbox)
    if not ids.get("success"):
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"It appears the deckbox {deckbox} doesn't exist",
      )
    wishlist_id = ids.get("wishlist")
    wishlist_cards_dict = await MongoClient.get_deckbox_cards_dict(
        deckbox_id=wishlist_id,
        wishlist=True,
    )
    wishlist_cards_list = list(wishlist_cards_dict.keys())
    if len(wishlist_cards_list) > 10:
      cards_chunks = await Utils.split_list_into_chunks(
          input_list=wishlist_cards_list,
          max_length=10,
      )
      print(f"CARD CHUNKS: {cards_chunks}")
      results = []
      for chunk in cards_chunks:
        chunk_result = await cls.wish_for_cards(
            chat_id=chat_id,
            received_cards=chunk,
            telegram_name=telegram_name,
        )
        results.append(chunk_result)
      return results
    else:
      result = await cls.wish_for_cards(
          chat_id=chat_id,
          received_cards=wishlist_cards_list,
          telegram_name=telegram_name,
      )
      return result

  @classmethod
  async def search_for_cards(
      cls,
      chat_id: str,
      received_cards: list,
      telegram_name: str,
  ):
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          status=False,
      )
    # Get the user subscriptions
    sub_dict = await MongoClient.get_user_subscriptions(
        telegram=telegram_name,
    )
    if not sub_dict:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You are not subscribed to any deckboxes!",
      )
    # Get the tradelist ID's of the subscriptions
    deckbox_name_matcher = {}
    sub_list = list(sub_dict.keys())
    trade_lists = []
    for deckbox in sub_list:
      ids = await Deckbox.get_deckbox_ids_from_account(account_name=deckbox)
      tradelist_id = ids.get("tradelist")
      trade_lists.append(tradelist_id)
      deckbox_name_matcher[tradelist_id] = deckbox
    # Find cards in tradelists
    found_cards_object = {}
    for deckbox_id in trade_lists:
      account = deckbox_name_matcher.get(deckbox_id)
      recache_deckbox = await cls.add_deckbox_to_mongo(
          deckbox_id=deckbox_id,
          account_name=account,
          tradelist=True,
      )
      if not recache_deckbox:
        return Utils.generate_outgoing_message(
            command="menu",
            chat_id=chat_id,
            message_text=(
                f"Failed to re-cache deckbox {account}. Please try again"
            ),
        )
      found_cards_object[deckbox_id] = []
      cards = await MongoClient.get_deckbox_cards_dict(
          deckbox_id=deckbox_id,
          tradelist=True,
      )
      cards_list = list(cards.keys())
      # Check every card the user entered
      for card in received_cards:
        lower_card = card.lower()
        first_letter = lower_card[0]
        first_index = await Utils.find_letter_index(
            input_list=cards_list,
            letter=first_letter,
        )
        # If the letter exists in the list start looking for cards
        if first_index is not None:
          cut_list = cards_list[first_index:]
          find = await cls.look_for_card_in_list(
              card_name=lower_card,
              card_list=cut_list,
          )
          # If cards were found add them to the dict to generate a message
          if find:
            for found_card in find:
              found_cards_object[deckbox_id].append(
                  (found_card, cards[found_card])
              )
    message = await Utils.construct_found_message(
        found_object=found_cards_object,
        deckbox_names=deckbox_name_matcher,
    )
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=message,
    )

  @classmethod
  async def wish_for_cards(
      cls,
      chat_id: str,
      received_cards: list,
      telegram_name: str,
  ):
    # Check if the user exists in mongo db
    user_exists = await MongoClient.check_if_user_exists(
        telegram_name=telegram_name,
    )
    if not user_exists:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You need to register first! Use /reg to register.",
          status=False,
      )
    # Get the user subscriptions
    sub_dict = await MongoClient.get_user_subscriptions(
        telegram=telegram_name,
    )
    if not sub_dict:
      return Utils.generate_outgoing_message(
          command="menu",
          chat_id=chat_id,
          message_text=f"You are not subscribed to any deckboxes!",
      )
    # Get the tradelist ID's of the subscriptions
    deckbox_name_matcher = {}
    sub_list = list(sub_dict.keys())
    trade_lists = []
    for deckbox in sub_list:
      ids = await Deckbox.get_deckbox_ids_from_account(account_name=deckbox)
      tradelist_id = ids.get("tradelist")
      trade_lists.append(tradelist_id)
      deckbox_name_matcher[tradelist_id] = deckbox
    # Find cards in tradelists
    found_cards_object = {}
    for deckbox_id in trade_lists:
      account = deckbox_name_matcher.get(deckbox_id)
      recache_deckbox = await cls.add_deckbox_to_mongo(
          deckbox_id=deckbox_id,
          account_name=account,
          tradelist=True,
      )
      if not recache_deckbox:
        return Utils.generate_outgoing_message(
            command="menu",
            chat_id=chat_id,
            message_text=(
                f"Failed to re-cache deckbox {account}. Please try again"
            ),
        )
      found_cards_object[deckbox_id] = []
      cards_dict = await MongoClient.get_deckbox_cards_dict(
          deckbox_id=deckbox_id,
          tradelist=True,
      )
      # Check every card the user entered
      for card in received_cards:
        lower_card = card.lower()
        found = cards_dict.get(lower_card)
        if found:
          found_cards_object[deckbox_id].append(
              (lower_card, cards_dict[lower_card])
          )
    message = await Utils.construct_found_message(
        found_object=found_cards_object,
        deckbox_names=deckbox_name_matcher,
    )
    return Utils.generate_outgoing_message(
        command="menu",
        chat_id=chat_id,
        message_text=message,
    )

  @classmethod
  async def resolve_command(
      cls,
      chat_id: str,
      command: str,
      message_text: str,
  ):
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
      # Registering a deckbox tradelist for a user
      case "regdeckbox":
        return await cls.add_deckbox_to_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      # Checking current registered deckbox tradelist
      case "mydeckbox":
        return await cls.check_user_deckbox(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "updatedeckbox":
        return await cls.update_user_deckbox(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "dbsub":
        return await cls.add_subscription_to_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "dbunsub":
        return await cls.remove_subscription_from_user(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "mydeckboxsubs":
        return await cls.check_user_deckbox_subscriptions(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "search":
        return await cls.bulk_search_cards(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "wish":
        return await cls.search_cards_from_wishlist(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "start":
        return await cls.get_user_menu(
            chat_id=chat_id,
            message_text=message_text,
        )
      case "edhdanas":
        return await cls.edh_danas_send_poll(
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
