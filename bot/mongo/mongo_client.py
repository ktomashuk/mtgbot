"""Module for working with Mongo DB.
"""
import motor.motor_asyncio
from bot.config import config
from bson import ObjectId
from datetime import datetime

class MongoClient:
  mongo_client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_CONNECTION)
  db = mongo_client.mtgbot
  users_colletion = db.users
  deckbox_tradelist_colletion = db.deckbox_tradelists
  deckbox_wishlist_collection = db.deckbox_wishlists
  edh_danas_collection = db.edh_danas
  quiz_collection = db.quiz
  status_collection = db.status
  stores_collection = db.stores
  league_collection = db.league
  league_invite_collection = db.league_invites
  league_players_collection = db.league_players
  league_matches_collection = db.league_matches

  @classmethod
  async def get_user_data(
      cls,
      telegram: str | None = None,
      discord: str | None = None,
      deckbox: str | None = None,
      moxfield: str | None = None,
  ) -> dict | None:
    """Fetches a user with a given name from the "users" collection.

    Args:
      telegram: telegram username to get
      discord: discord username to get
      deckbox: deckbox username to get
      moxfield: moxfield username to get
    Returns:
      A dict with user details or None if user doesn't exist
    """
    user = None
    if telegram:
      user = await cls.users_colletion.find_one({"telegram": telegram.lower()})
    elif discord:
      user = await cls.users_colletion.find_one({"discord": discord.lower()})
    elif deckbox:
      user = await cls.users_colletion.find_one(
          {"deckbox_name": deckbox.lower()}
      )
    elif moxfield:
      user = await cls.users_colletion.find_one(
          {"moxfield_name": moxfield.lower()}
      )
    return user

  @classmethod
  async def get_deckbox_data(
      cls,
      deckbox_id: str,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> dict | None:
    """Fetches a deckbox with a given ID.

    Args:
      deckbox: ID of the deckbox tradelist to get
      tradelist: set to True when fetching a tradelist
      wishlist: set to True when fetching a wishlist
    Returns:
      A dict with list details or None if list doesn't exist
    """
    result = None
    if tradelist:
      result = await cls.deckbox_tradelist_colletion.find_one(
        {"deckbox_id": deckbox_id.lower()}
      )
    if wishlist:
      result = await cls.deckbox_wishlist_collection.find_one(
        {"deckbox_id": deckbox_id.lower()}
      )
    return result

  @classmethod
  async def match_deckbox_tradelist_ids_to_names(
      cls,
      deckbox_names: list[str],
  ) -> dict | None:
    """Creates a dict that has deckbox IDs as keys and account names as values.

    Args:
      deckbox_names: a list of deckbox account names
    Returns:
      A dict matching deckbox IDs to account names
    """
    query = {"account_name": {"$in": deckbox_names}}
    cursor = cls.deckbox_tradelist_colletion.find(query)
    results = {}
    async for document in cursor:
      deckbox_id = document.get("deckbox_id")
      name = document.get("account_name")
      # Only add to results if deckbox_id is in the input list
      if name in deckbox_names:
          results[deckbox_id] = name
    return results

  @classmethod
  async def check_if_user_exists(
      cls,
      telegram_name: str | None = None,
      discord_name: str | None = None,
  ) -> bool:
    """Tries to fetch a user with a given name from the "users" collection and
    checks if the user exists.

    Args:
      telegram_name: telegram username to check
      discord_name: discord username to check
    Returns:
      True if the user exists, False if they don't
    """
    user = None
    if telegram_name and discord_name:
      user = await cls.users_colletion.find_one(
          {"telegram": telegram_name.lower(), "discord": discord_name.lower()}
      )
    elif telegram_name:
      user = await cls.users_colletion.find_one(
          {"telegram": telegram_name.lower()}
      )
    elif discord_name:
      user = await cls.users_colletion.find_one(
          {"discord": discord_name.lower()}
      )
    return user is not None

  @classmethod
  async def check_if_deckbox_exists(
      cls,
      deckbox_id: str,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> bool:
    """Tries to fetch a deckbox with a given ID and checks if it exists.

    Args:
      deckbox_id: tradelist deckbox ID to check
      tradelist: set to True when checking a tradelist
      wishlist: set to True when checking a wishlist
    Returns:
      True if the deckbox list exists, False if it doesn't
    """
    result = None
    if tradelist:
      result = await cls.deckbox_tradelist_colletion.find_one(
          {"deckbox_id": deckbox_id.lower()}
      )
    if wishlist:
      result = await cls.deckbox_wishlist_collection.find_one(
          {"deckbox_id": deckbox_id.lower()}
      )
    return result is not None

  @classmethod
  async def check_deckbox_cache(
      cls,
      deckbox_id: str,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> bool:
    """Tries to fetch a deckbox with a given ID and checks when it was cached.

    Args:
      deckbox: deckbox ID to check
      tradelist: set to True when checking a tradelist cache
      wishlist: set to True when checking a wishlist cache
    Returns:
      True if the deckbox cache is younger than 12 hours, False if it isn't
    """
    result = None
    if tradelist:
      result = await cls.deckbox_tradelist_colletion.find_one(
          {"deckbox_id": deckbox_id.lower()}
      )
    if wishlist:
      result = await cls.deckbox_wishlist_collection.find_one(
          {"deckbox_id": deckbox_id.lower()}
      )
    if not result:
      return False
    cache_date = result.get("last_cached")
    converted_date = datetime.strptime(cache_date, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    time_difference = now - converted_date
    minutes_passed = round(time_difference.total_seconds() / 60, 2)
    return minutes_passed < 1500

  @classmethod
  async def add_user(
      cls,
      object: dict,
  ) -> bool:
    """Adds a new object with the user data to the "users" collection.

    Args:
      object: a dictionary with user data to be added
    Returns:
      A boolean with status of the operation
    """
    result = await cls.users_colletion.insert_one(object)
    if result:
      return result.acknowledged
    else:
      return False

  @classmethod
  async def add_quiz_object(
      cls,
      card_name: str,
      message_id: str,
  ) -> bool:
    """Adds a new object with the quiz data to the "quiz" collection.

    Args:
      object: a dictionary with quiz data to be added
    Returns:
      A bool with status of the operation
    """
    object = {
        "card_name": card_name,
        "message_id": message_id,
    }
    result = await cls.quiz_collection.insert_one(object)
    if result:
      return result.acknowledged
    else:
      return False

  @classmethod
  async def get_quiz_object(
      cls,
      message_id: str,
  ) -> dict:
    """Fetches the quiz data by message ID.

    Args:
      message_id: message ID of the quiz object
    Returns:
      A dict with quiz data
    """
    result = await cls.quiz_collection.find_one(
        {"message_id": message_id}
    )
    return result

  @classmethod
  async def add_deckbox(
      cls,
      object: dict,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> bool:
    """Adds a new object with the deckbox data to the 
    "deckbox_tradelists" or "deckbox_wishlists" collection.

    Args:
      object: a dictionary with deckbox tradelist data to be added
      tradelist: set to True when adding a tradelists
      wishlist: set to True when adding a wishlists
    Returns:
      A boolean with the status of the operation
    """
    result = None
    if tradelist:
      result = await cls.deckbox_tradelist_colletion.insert_one(object)
    if wishlist:
      result = await cls.deckbox_wishlist_collection.insert_one(object)
    return result.acknowledged if result else result

  @classmethod
  async def add_edh_danas(
      cls,
      object: dict,
  ) -> bool:
    """Adds a new object with the edh_danas data to the "edh_danas" collection.

    Args:
      object: a dictionary with deckbox tradelist data to be added
    Returns:
      A boolean with the status of the operation
    """
    result = None
    result = await cls.edh_danas_collection.insert_one(object)
    return result.acknowledged if result else result

  @classmethod
  async def check_edh_danas(
      cls,
      timestamp: str,
  ) -> dict | None:
    """Tries to fetch a edh danas object with a given timestamp.

    Args:
      timestamp: timestamp to look for in '%Y-%m-%d' format
    Returns:
      A dict with edh danas data or None if it doesn't exist
    """
    result = None
    result = await cls.edh_danas_collection.find_one(
        {"timestamp": timestamp}
    )
    return result

  @classmethod
  async def delete_edh_danas(
      cls,
      timestamp: str,
  ) -> bool:
    """Deletes a edh danas object with a given timestamp

    Args:
      timestamp: timestamp to look for in '%Y-%m-%d' format
    Returns:
      A boolean with status of the operation
    """
    latest_record = await cls.edh_danas_collection.find_one(
        {"timestamp": timestamp}
    )
    if latest_record is not None:
        # Delete the record using its _id
        delete_result = await cls.edh_danas_collection.delete_one(
            {'_id': ObjectId(latest_record['_id'])}
        )
        return delete_result.deleted_count > 0
    return False

  @classmethod
  async def update_deckbox(
      cls,
      deckbox: str,
      object: dict,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> (bool, str):
    """Updates the deckbox with new values.

    Args:
      deckbox: ID of the deckbox to update
      object: a dictionary with deckbox tradelist data to be added
      tradelist: set to True when updating a tradelists
      wishlist: set to True when updating a wishlists
    Returns:
      A tuple with a boolean status of the operation and a message
    """
    result = None
    if tradelist:
      result = await cls.deckbox_tradelist_colletion.update_one(
          {"deckbox_id": deckbox.lower()},
          {"$set": object}
      )
    if wishlist:
      result = await cls.deckbox_wishlist_collection.update_one(
          {"deckbox_id": deckbox.lower()},
          {"$set": object}
      )
    if not result:
      return (False, "Something went wrong! Please try again!")
    else:
      if result.modified_count > 0:
        return (True, f"Tradelist updated successfully.")
      else:
        return (True, "Nothing has changed.")

  @classmethod
  async def get_deckbox_name(
      cls,
      deckbox_id: str,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> str:
    """Fetches the account name for the chosen deckbox list ID.

    Args:
      deckbox: id of the deckbox list
      tradelist: set to True when searching for tradelists
      wishlist: set to True when searching for wishlists
    Returns:
      A string with the username associated with the decklist ID
    """
    account_name = ""
    if tradelist:
      result = await cls.deckbox_tradelist_colletion.find_one(
          {"deckbox_id": deckbox_id.lower()}
      )
      account_name = result.get("account_name")
    if wishlist:
      result = await cls.deckbox_wishlist_collection.find_one(
          {"deckbox_id": deckbox_id.lower()}
      )
      account_name = result.get("account_name")
    return account_name

  @classmethod
  async def get_deckbox_id(
      cls,
      deckbox_name: str,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> str:
    """Fetches the deckbox ID for the chosen account name.

    Args:
      deckbox_name: name of the deckbox account
      tradelist: set to True when searching for tradelists
      wishlist: set to True when searching for wishlists
    Returns:
      A string with the deckbox ID associated with the deckbox account name
    """
    deckbox_id = ""
    if tradelist:
      result = await cls.deckbox_tradelist_colletion.find_one(
          {"account_name": deckbox_name.lower()}
      )
      deckbox_id = result.get("deckbox_id", "")
    if wishlist:
      result = await cls.deckbox_wishlist_collection.find_one(
          {"account_name": deckbox_name.lower()}
      )
      deckbox_id = result.get("deckbox_id", "")
    return deckbox_id

  @classmethod
  async def get_deckbox_subscribers(
      cls,
      account_name: str,
  ) -> list[dict]:
    """Fetches all user objects of users subscribed to a certain deckbox.

    Args:
      account_name: name of the deckbox account
    Returns:
      A list of user objects
    """
    query = {f"deckbox_subscriptions.{account_name}": {"$exists": True}}
    cursor = cls.users_colletion.find(query)
    result_list = []
    async for user in cursor:
        result_list.append(user)
    return result_list

  @classmethod
  async def get_all_deckboxes(
      cls,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> dict:
    """Fetches all the deckboxes present in the DB.

    Args:
      tradelist: set to True when searching for tradelists
      wishlist: set to True when searching for wishlists
    Returns:
      A dict with deckbox IDs as keys and their account names as values
    """
    result_dict = {}
    if tradelist:
      cursor = cls.deckbox_tradelist_colletion.find({})
      async for document in cursor:
        deckbox_id = document.get("deckbox_id", "")
        account_name = document.get("account_name", "")
        if deckbox_id and account_name:
          result_dict[deckbox_id] = account_name
    if wishlist:
      cursor = cls.deckbox_wishlist_collection.find({})
      async for document in cursor:
        deckbox_id = document.get("deckbox_id", "")
        account_name = document.get("account_name", "")
        if deckbox_id and account_name:
          result_dict[deckbox_id] = account_name
    return result_dict

  @classmethod
  async def add_deckbox_to_user(
      cls,
      deckbox: str,
      telegram_name: str | None = None,
      discord_name: str | None = None,
  ) -> (bool, str):
    """Updates the "deckbox_name" key in the "users" collection for a
    given username.

    Args:
      deckbox: name of the deckbox account
      telegram_name: telegram username to add deckbox to
      discord_name: discord username to add deckbox to
    Returns:
      A tuple with the status of the transaction and a resulting message
    """
    result = None
    if telegram_name:
      result = await cls.users_colletion.update_one(
          {"telegram": telegram_name.lower()},
          {"$set": {"deckbox_name": deckbox.lower()}}
      )
    elif discord_name:
      result = await cls.users_colletion.update_one(
          {"discord": discord_name.lower()},
          {"$set": {"deckbox_name": deckbox.lower()}}
      )
    if not result:
      return (False, "Something went wrong! Please try again!")
    else:
      if result.modified_count > 0:
        return (True, f"Deckbox {deckbox.lower()} added successfully.")
      else:
        return (False, "That deckbox is already yours.")

  @classmethod
  async def add_chat_id_to_user(
      cls,
      chat_id: str,
      telegram_name: str | None = None,
      discord_name: str | None = None,
  ) -> bool:
    """Adds the "chat_id" to the user in the DB.

    Args:
      chat_ud: user's telegram chat ID
      telegram_name: telegram username to add chat id to
      discord_name: discord username to add chat id to
    Returns:
      A status of the transaction
    """
    result = None
    if telegram_name:
      result = await cls.users_colletion.update_one(
          {"telegram": telegram_name.lower()},
          {"$set": {"chat_id": chat_id}}
      )
    elif discord_name:
      result = await cls.users_colletion.update_one(
          {"discord": discord_name.lower()},
          {"$set": {"chat_id": chat_id}}
      )
    if not result:
      return False
    else:
      return result.modified_count > 0

  @classmethod
  async def add_subscription_to_user(
      cls,
      subscription_name: str,
      telegram: str | None = None,
      discord: str | None = None,
  ) -> bool:
    """Updates the "deckbox_subscriptions" key in the "users" collection for a
    given username with a new subscription.

    Args:
      subscription_name: name of the subscription to add
      telegram: telegram username to add subscription to
      discord: discord username to add subscription to
    Returns:
      A boolean with the status of the operation
    """
    update_field = f"deckbox_subscriptions.{subscription_name.lower()}"
    result = None
    if telegram:
      result = await cls.users_colletion.update_one(
          {"telegram": telegram.lower()},
          {"$set": {update_field: False}}
      )
    if discord:
      result = await cls.users_colletion.update_one(
          {"discord": discord.lower()},
          {"$set": {update_field: False}}
      )
    return result

  @classmethod
  async def remove_subscription_from_user(
      cls,
      subscription_name: str,
      telegram: str | None = None,
      discord: str | None = None,
  ) -> bool:
    """Updates the "deckbox_subscriptions" key in the "users" collection for a
    given username by removing an existing subscription.

    Args:
      subscription_name: name of the subscription to remove
      telegram: telegram username to remove subscription from
      discord: discord username to remove subscription from
    Returns:
      A boolean with the status of the operation
    """
    update_field = f"deckbox_subscriptions.{subscription_name.lower()}"
    result = None
    if telegram:
      result = await cls.users_colletion.update_one(
          {"telegram": telegram.lower()},
          {"$unset": {update_field: False}}
      )
    if discord:
      result = await cls.users_colletion.update_one(
          {"discord": discord.lower()},
          {"$unset": {update_field: False}}
      )
    return result

  @classmethod
  async def get_user_subscriptions(
      cls,
      telegram: str | None = None,
      discord: str | None = None,
  ) -> dict | None:
    """Fetches a list of user subscriptions.

    Args:
      telegram: telegram username to get subscriptions
      discord: discord username to get subscriptions
    Returns:
      A dict with subscriptions or None if it doesn't exist
    """
    user_data = None
    if telegram:
      user_data = await cls.get_user_data(telegram=telegram.lower())
    if discord:
      user_data = await cls.get_user_data(discord=discord.lower())
    if user_data:
      subscriptions = user_data.get("deckbox_subscriptions")
      return subscriptions
    return None

  @classmethod
  async def get_deckbox_cards_dict(
      cls,
      deckbox_id: str,
      tradelist: bool = False,
      wishlist: bool = False,
  ) -> dict:
    """Fetches a list of cards from a chosen deckbox ID.

    Args:
      deckbox_id: id of the deckbox to get cards from
      telegram: telegram username to get subscriptions
      discord: discord username to get subscriptions
    Returns:
      A dict with cards or None if it doesn't exist
    """
    result = None
    card_dict = {}
    if tradelist:
      result = await cls.deckbox_tradelist_colletion.find_one(
        {"deckbox_id": deckbox_id.lower()}
      )
      card_dict = result.get("cards", {})
    if wishlist:
      result = await cls.deckbox_wishlist_collection.find_one(
        {"deckbox_id": deckbox_id.lower()}
      )
      card_dict = result.get("cards", {})
    return card_dict

  @classmethod
  async def add_status(
      cls,
      object: dict,
  ) -> bool:
    """Adds a new object with the user data to the "status" collection.

    Args:
      object: a dictionary with status data to be added
    Returns:
      A boolean with status of the operation
    """
    result = await cls.status_collection.insert_one(object)
    if result:
      return result.acknowledged
    else:
      return False

  @classmethod
  async def add_store(
      cls,
      object: dict,
  ) -> bool:
    """Adds a new object with the user data to the "stores" collection.

    Args:
      object: a dictionary with store data to be added
    Returns:
      A boolean with status of the operation
    """
    result = await cls.stores_collection.insert_one(object)
    if result:
      return result.acknowledged
    else:
      return False

  @classmethod
  async def check_if_store_exists(
      cls,
      store_name: str,
  ) -> bool:
    """Tries to fetch a store with a given name from the "stores" collection and
    checks if the store exists.

    Args:
      store_name: store name to check
    Returns:
      True if the user exists, False if they don't
    """
    store = None
    store = await cls.stores_collection.find_one(
        {"name": store_name.lower()}
    )
    return store is not None

  @classmethod
  async def update_store(
      cls,
      store_name: str,
      cards: dict,
  ) -> bool:
    """Updates the store with new cards.

    Args:
      store_name: name of the store to update
      cards: a dictionary with cards data to be added
    Returns:
      A tuple with a boolean status of the operation and a message
    """
    result = await cls.stores_collection.update_one(
        {"name": store_name.lower()},
        {"$set": {"cards": cards}}
    )
    if not result:
      return False
    else:
      return True

  @classmethod
  async def add_store_subscription_to_user(
      cls,
      subscription_name: str,
      telegram: str | None = None,
      discord: str | None = None,
  ) -> bool:
    """Updates the "store_subscriptions" key in the "users" collection for a
    given username with a new subscription.

    Args:
      subscription_name: name of the subscription to add
      telegram: telegram username to add subscription to
      discord: discord username to add subscription to
    Returns:
      A boolean with the status of the operation
    """
    update_field = f"store_subscriptions.{subscription_name.lower()}"
    result = None
    if telegram:
      result = await cls.users_colletion.update_one(
          {"telegram": telegram.lower()},
          {"$set": {update_field: False}}
      )
    if discord:
      result = await cls.users_colletion.update_one(
          {"discord": discord.lower()},
          {"$set": {update_field: False}}
      )
    return result

  @classmethod
  async def remove_store_subscription_from_user(
      cls,
      subscription_name: str,
      telegram: str | None = None,
      discord: str | None = None,
  ) -> bool:
    """Updates the "store_subscriptions" key in the "users" collection for a
    given username by removing an existing subscription.

    Args:
      subscription_name: name of the subscription to remove
      telegram: telegram username to remove subscription from
      discord: discord username to remove subscription from
    Returns:
      A boolean with the status of the operation
    """
    update_field = f"store_subscriptions.{subscription_name.lower()}"
    result = None
    if telegram:
      result = await cls.users_colletion.update_one(
          {"telegram": telegram.lower()},
          {"$unset": {update_field: False}}
      )
    if discord:
      result = await cls.users_colletion.update_one(
          {"discord": discord.lower()},
          {"$unset": {update_field: False}}
      )
    return result

  @classmethod
  async def get_store_cards_dict(
      cls,
      store_name: str,
  ) -> dict:
    """Fetches a list of cards from a chosen store.

    Args:
      store_name: name of the store to get cards from
    Returns:
      A dict with cards or None if it doesn't exist
    """
    result = None
    card_dict = {}
    result = await cls.stores_collection.find_one(
      {"name": store_name.lower()}
    )
    card_dict = result.get("cards", {})
    return card_dict

  @classmethod
  async def get_user_store_subscriptions(
      cls,
      telegram: str | None = None,
      discord: str | None = None,
  ) -> dict | None:
    """Fetches a list of user store subscriptions.

    Args:
      telegram: telegram username to get subscriptions
      discord: discord username to get subscriptions
    Returns:
      A dict with subscriptions or None if it doesn't exist
    """
    user_data = None
    if telegram:
      user_data = await cls.get_user_data(telegram=telegram.lower())
    if discord:
      user_data = await cls.get_user_data(discord=discord.lower())
    if user_data:
      subscriptions = user_data.get("store_subscriptions")
      return subscriptions
    return None
