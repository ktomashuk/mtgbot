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
      A dict with card json data
    """
    url = SCRYFALL_GET_CARD_URL.format(name=card_name)
    response = await HttpClient.HTTP_SESSION.get(url=url)
    response_json = await response.json()
    return response_json

  @classmethod
  async def get_random_card(
      cls,
      non_zero_cmc: bool = False,
  ) -> dict | None:
    """Fetches random card info from scryfall API.

    Args:
      non_zero_cmc: set to True to fetch only cards with CMC >= 1

    Returns:
      A dict with card json data
    """
    url = SCRYFALL_GET_RANDOM_CARD_URL
    if non_zero_cmc:
      url += "?q=cmc%3E%3D1"
    response = await HttpClient.HTTP_SESSION.get(url=url)
    if response.status == 200:
      response_json = await response.json()
      if response_json.get("object") == "card":
        return response_json
      return None
    else:
      return None

  @classmethod
  async def get_card_image(
      cls,
      card_name: str,
      random_card: bool = False,
      non_zero_cmc: bool = False,
  ) -> list[str] | str | None:
    """Gets card images for a card with the chosen name.

    Args:
      card_name: name of the card
      random_card: set to True to fetch a random card
      non_zero_cmc: set to True to fetch only cards with CMC >= 1

    Returns:
      A list of strings with the image urls (empty if card doesn't exist)
    """
    if random_card:
      response = await cls.get_random_card(non_zero_cmc=non_zero_cmc)
    else:
      response = await cls.get_card(card_name=card_name)

    results = []
    if not response:
      return results
    response_object = response.get("object")
    response_type = response.get("type")
    if response_object == "error" and response_type == "ambiguous":
      return "ambiguous"
    elif response_object == "error" and not response_type:
      return "not_found"
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
  async def get_card_image_art(
      cls,
      non_zero_cmc: bool = False,
  ) -> dict | None:
    """Fetches cropped art of a random card from scryfall.

    Args:
      non_zero_cmc: set to True to fetch only cards with CMC >= 1
    Returns:
      A dict with card name and art
    """
    response = await cls.get_random_card(non_zero_cmc=non_zero_cmc)
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
    """Fetches full card url of a chosen card.

    Args:
      card_name: name of the card
    Returns:
      A string with the card url or None if card doesn't exist
    """
    response = await cls.get_card(card_name=card_name)
    response_object = response.get("object")
    response_type = response.get("type")
    if response_object == "error" and response_type == "ambiguous":
      return "ambiguous"
    elif response_object == "error" and not response_type:
      return "not_found"
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
    response_object = response.get("object")
    response_type = response.get("type")
    if response_object == "error" and response_type == "ambiguous":
      return "ambiguous"
    elif response_object == "error" and not response_type:
      return "not_found"
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
