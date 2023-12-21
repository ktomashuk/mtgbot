"""Module for working with scryfall API.
"""
from bot.config.urls import SCRYFALL_GET_CARD_URL, SCRYFALL_GET_RANDOM_CARD_URL
from bot.config.http_client import HttpClient

class ScryfallFetcher:

  @classmethod
  async def get_card(cls, card_name: str) -> dict | None:
    """Fetches card info from scryfall API by name

    Args:
      card_name: name of the card
    Returns:
      A Response object or None if card doesn't exist
    """
    url = SCRYFALL_GET_CARD_URL.format(name=card_name)
    response = await HttpClient.HTTP_SESSION.get(url=url)
    if response.status == 200:
      response_json = await response.json()
      if response_json.get("object") == "card":
        return response_json
      return None
    else:
      return None

  @classmethod
  async def get_random_card(cls) -> dict | None:
    """Fetches random card info from scryfall API by name

    Returns:
      A Response object or None if card doesn't exist
    """
    url = SCRYFALL_GET_RANDOM_CARD_URL
    response = await HttpClient.HTTP_SESSION.get(url=url)
    if response.status == 200:
      response_json = await response.json()
      if response_json.get("object") == "card":
        return response_json
      return None
    else:
      return None

  @classmethod
  async def get_card_image(cls, card_name: str) -> list[str] | None:
    """Fetches card info from scryfall API by name

    Args:
      card_name: name of the card
    Returns:
      A string with the image url or None if card doesn't exist
    """
    response = await cls.get_card(card_name=card_name)
    results = []
    if not response:
      return results
    faces = response.get("card_faces", None)
    image_uri = response.get("image_uris", None)
    if faces:
      for face in faces:
        image = face["image_uris"]["normal"]
        results.append(image)
    if image_uri:
      image = image_uri["normal"]
      results.append(image)
    return results

  @classmethod
  async def get_card_image_art(cls) -> dict | None:
    """Fetches card info from scryfall API by name

    Args:
      card_name: name of the card
    Returns:
      A string with the image url or None if card doesn't exist
    """
    response = await cls.get_random_card()
    image_url = None
    if response:
      image_url = response.get("image_uris", {})
      card_name = response.get("name")
      art = image_url.get("art_crop")
      return {
          "card_name": card_name,
          "art": art,
      }
    return None

  @classmethod
  async def get_card_url(cls, card_name: str) -> str | None:
    """Fetches card info from scryfall API by name

    Args:
      card_name: name of the card
    Returns:
      A string with the image url or None if card doesn't exist
    """
    response = await cls.get_card(card_name=card_name)
    card_url = None
    if response:
      card_url = response.get("scryfall_uri")
    return card_url

  @classmethod
  async def get_card_prices(cls, card_name: str) -> str | None:
    """Fetches card prices from scryfall API by name

    Args:
      card_name: name of the card
    Returns:
      A string with prices or None if card doesn't exist
    """
    response = await cls.get_card(card_name=card_name)
    text = None
    if response:
      full_name = response.get("name")
      scryfall_prices = response.get("prices")
      usd = scryfall_prices.get("usd")
      usd_foil = scryfall_prices.get("usd_foil")
      text = (
          f"Scryfall prices for '{full_name}':\n"
          f"Regular: ${usd if usd else "n/a"}\n"
          f"Foil: ${usd_foil if usd_foil else "n/a"}"
      )
    return text
