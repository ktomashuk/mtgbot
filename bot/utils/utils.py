import json
from bot.deckbox.deckbox import Deckbox
from bot.mongo.mongo_client import MongoClient
from datetime import datetime, timedelta

class Utils:

  @classmethod
  def generate_outgoing_message(
      cls,
      command: str,
      chat_id: str,
      message_text: str,
      options: list[str] | dict | None = None,
      status: bool = True,
  ) -> bytes:
    """Generates a message to be sent to a queue.

    Args:
      command: a string with a command to send
      chat_id: id of the chat to send response to
      message_text: message that will be sent
      options: additional options to send
      status: status check (mostly for checking registration)
    Returns:
      A dict encoded into bytes
    """
    message = {
      "command": command,
      "chat_id": chat_id,
      "text": message_text,
      "status": status,
      "options": options,
    }
    json_message = json.dumps(message)
    message_bytes = json_message.encode("UTF-8")
    return message_bytes

  @classmethod
  async def find_letter_index(
      cls,
      input_list: list[str],
      letter: str,
  ) -> int | None:
    """Performs a binary search on list of strings to find the first index
    where a word starts with a given letter.

    Args:
      input_list: ordered list of strings
      letter: the letter to look for
    Returns:
      An index of a first found word starting with a letter or None if not found
    """
    left, right = 0, len(input_list) - 1
    result = -1
    while left <= right:
        mid = (left + right) // 2
        if input_list[mid].startswith(letter):
            result = mid
            right = mid - 1
        elif input_list[mid] < letter:
            left = mid + 1
        else:
            right = mid - 1
    return result if result != -1 else None

  @classmethod
  async def construct_found_message(
      cls,
      found_object: dict,
      deckbox_names: dict,
  ) -> str:
    """Performs a binary search on list of strings to find the first index
    where a word starts with a given letter.

    Args:
      input_list: ordered list of strings
      letter: the letter to look for
    Returns:
      An index of a first found word starting with a letter or None if not found
    """
    result_message = ""
    deckbox_ids = found_object.keys()
    for deckbox_id in deckbox_ids:
      if found_object[deckbox_id]:
        deckbox_name = deckbox_names[deckbox_id]
        deckbox_message = f"\nDeckbox: <b>{deckbox_name}</b>\n"
        user_data = await MongoClient.get_user_data(deckbox=deckbox_name)
        if user_data:
          telegram_name = user_data.get("telegram")
          discord_name = user_data.get("discord")
          if telegram_name:
            deckbox_message += f"Telegram: {telegram_name}\n"
          if discord_name:
            deckbox_message += f"Discord: {discord_name}\n"
          if not telegram_name and not discord_name:
            deckbox_message += "\n"
        found_cards = found_object[deckbox_id]
        for card in found_cards:
          (name, count) = card
          card_url = await Deckbox.create_deckbox_url(
              deckbox_id=deckbox_id,
              card_name=name,
          )
          card_message = f"<a href='{card_url}'>{name}</a>: {count}\n"
          deckbox_message += card_message
        result_message += deckbox_message
    if result_message == "":
      result_message = "No cards were found :("
    return result_message

  @classmethod
  async def split_list_into_chunks(
      cls,
      input_list: list,
      max_length: int,
  ) -> str:
    """Splits a list into a list of lists with maximum length.

    Args:
      input_list: a list to be split
      max_length: maximum length of resulting 
    Returns:
      A list of lists
    """
    if len(input_list) < 11:
      return input_list
    result = []
    while input_list:
      result.append(input_list[:max_length])
      input_list = input_list[max_length:]
    return result

  @classmethod
  def check_if_next_day(
      cls,
      current_day: str,
      previous_day: str,
  ) -> bool:
    """Checks if current date is at least 1 day later than previous one.

    Args:
      current_day: current date in a string
      previous_day: previous date in a string
    Returns:
      A boolean with the status
    """
    current_date = datetime.strptime(current_day, "%Y-%m-%d %H:%M:%S")
    previous_date = datetime.strptime(previous_day, "%Y-%m-%d %H:%M:%S")
    return current_date.date() >= previous_date.date() + timedelta(days=1)
