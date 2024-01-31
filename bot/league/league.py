"""Module for manipulating leagues.
"""
from datetime import datetime
from bot.mongo.mongo_client import MongoClient
from bot.telegram.bot import MagicBot


class League:

  @classmethod
  async def create_league(
      cls,
      league_name: str,
      league_length: int,
      league_id: str,
  ) -> bool:
    """Creates a new league in the DB.

    Args:
      league_name: name of the league
      league_length: length of the league in weeks
      league_id: ID of the league

    Returns:
      A bool with the result of the operation
    """
    now = datetime.now()
    league_start = now.strftime("%Y-%m-%d")
    league_object = {
        "league_name": league_name,
        "league_id": league_id,
        "start_date": league_start,
        "total_duration_weeks": league_length,
        "current_week": 1,
        "active": True,
        "subscribed_channels": {},
    }
    league_added = await MongoClient.add_league(object=league_object)
    return league_added

  @classmethod
  async def create_league_invite(
      cls,
      league_id: str,
      invite_id: str,
  ) -> bool:
    """Creates a new league invite in the DB.

    Args:
      league_id: ID of the league
      invite_id: ID of the league invite

    Returns:
      A bool with the result of the operation
    """
    league_invite_object = {
        "league_id": league_id,
        "invite_code": invite_id,
    }
    invite_added = await MongoClient.add_league_invite(
        object=league_invite_object,
    )
    return invite_added

  @classmethod
  async def create_league_player(
      cls,
      telegram: str,
      chat_id: int,
      league_id: str,
  ) -> bool:
    """Creates a new player in the DB.

    Args:
      telegram: name of the player
      chat_id: chat id of the player
      league_id: ID of the league

    Returns:
      A bool with the result of the operation
    """
    now = datetime.now()
    date_joined = now.strftime("%d.%m.%Y")
    player_object = {
        "league_id": league_id,
        "telegram": telegram.lower(),
        "chat_id": chat_id,
        "date_joined": date_joined,
        "total_points": 0,
        "standing_matches_played": 0,
        "standing_wins": 0,
        "standing_losses": 0,
        "total_played": 0,
        "total_wins": 0,
        "total_losses": 0,
        "win_streak": 0,
    }
    player_added = await MongoClient.add_league_player(object=player_object)
    return player_added

  @classmethod
  async def get_league_stats(
      cls,
      league_id: str,
  ) -> str:
    """Fetches a league stats from the DB and creates a text message.

    Args:
      league_id: ID of the league

    Returns:
      A bool with the result of the operation
    """
    league_data = await MongoClient.get_league(league_id=league_id)
    league_name = league_data.get("league_name")
    current_week = league_data.get("current_week")
    total_weeks = league_data.get("total_duration_weeks")
    message = (
        f"{league_name}\n"
        f"Current week: {current_week}/{total_weeks}\n"
    )
    return message

  @classmethod
  async def create_league_match(
      cls,
      player_one: str,
      player_two: str,
      result: str,
      league_id: str,
      player_one_standing: bool,
      player_two_standing: bool,
  ) -> bool:
    """Creates a new match in the DB.

    Args:
      player_one: name of the first player
      player_two: name of the second player
      result: result string
      league_id: ID of the league
      player_one_standing: is this a standing match for player one
      player_two_standing: is this a standing match for player two

    Returns:
      A bool with the result of the operation
    """
    now = datetime.now()
    date_played = now.strftime("%d.%m.%Y %H:%M")
    results = result.split("-")
    player_one_score = int(results[0])
    player_two_score = int(results[1])
    if player_one_score > player_two_score:
      winner = player_one
    else:
      winner = player_two
    match_object = {
        "league_id": league_id,
        "player_one": player_one,
        "player_two": player_two,
        "player_one_score": player_one_score,
        "player_two_score": player_two_score,
        "winner": winner,
        "result": result,
        "date_played": date_played,
        "standings": {
            player_one: player_one_standing,
            player_two: player_two_standing,
        },
    }
    match_added = await MongoClient.add_league_match(object=match_object)
    return match_added

  @classmethod
  async def league_broadcast_message(
      cls,
      message: str,
      league_id: str,
  ) -> None:
    """Broadcasts a message to all channels who subscribe to the league.

    Args:
      message: text of the message
      league_id: ID of the league
    """
    print(f"Broadcasting a message to league: {league_id}")
    league = await MongoClient.get_league(league_id=league_id)
    channels = league.get("subscribed_channels")
    for channel in channels.keys():
      await MagicBot.send_message_to_user(
          chat_id=channel,
          message=message,
      )
