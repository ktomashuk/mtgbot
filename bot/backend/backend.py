from bot.deckbox.deckbox import Deckbox
from bot.mongo.mongo_client import MongoClient
from bot.utils.utils import Utils
from bot.deckbox.deckbox import Deckbox

class Backend:

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
    sub_list = list(sub_dict.keys())
    deckboxes = await MongoClient.match_deckbox_tradelist_ids_to_names(
        deckbox_names=sub_list,
    )
    trade_lists = list(deckboxes.keys())
    # Find cards in tradelists
    found_cards_object = {}
    for deckbox_id in trade_lists:
      account = deckboxes.get(deckbox_id)
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
    return found_cards_object

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
    sub_list = list(sub_dict.keys())
    deckboxes = await MongoClient.match_deckbox_tradelist_ids_to_names(
        deckbox_names=sub_list,
    )
    trade_lists = list(deckboxes.keys())
    # Find cards in tradelists
    found_cards_object = {}
    for deckbox_id in trade_lists:
      account = deckboxes.get(deckbox_id)
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
    return found_cards_object
