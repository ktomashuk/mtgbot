"""A module for scraping the mtgtop8.com site.
"""
import random
from bot.config.urls import (
    MTGTOP8_PAUPER_FORMAT_URL,
    MTGTOP8_MODERN_FORMAT_URL
)
from bot.config.http_client import HttpClient
from bs4 import BeautifulSoup
from enum import Enum

class Formats(Enum):
  PAUPER = "pauper"
  MODERN = "modern"
  STANDARD = "standard"

class MtgTop8:

  @classmethod
  async def get_format_page(
      cls,
      format: Formats,
  ) -> str:
    """Fetches the text of a main page for a chosen format.

    Args:
      format: the format to fetch
    Returns:
      A string with the HTML of the page
    """
    match format:
      case Formats.PAUPER:
        url = MTGTOP8_PAUPER_FORMAT_URL
      case Formats.MODERN:
        url = MTGTOP8_MODERN_FORMAT_URL
    response = await HttpClient.HTTP_SESSION.get(url=url)
    response_text = await response.text()
    return response_text

  @classmethod
  async def get_decks_from_tournament_page(
      cls,
      tournament_link: str,
  ) -> list[dict[str]]:
    """Fetches the decks from tournament page.

    Args:
      tournament_link: the end of the URL for a specific tournament
    Returns:
      A list of dictionaries composed of decks name and deck link
    """
    decks = []
    url = f"https://mtgtop8.com/{tournament_link}"
    response = await HttpClient.HTTP_SESSION.get(url=url)
    response_text = await response.text()
    soup = BeautifulSoup(response_text, 'html.parser')
    divs = soup.find_all(
        "div",
        style=lambda style: style 
        and "width:100%;padding-left:4px;margin-bottom:4px;" in style
    )
    for div in divs:
      deck_name = div.text.strip()
      link = div.find("a")
      if href:= link.get("href"):
        deck = {
            "name": deck_name,
            "link": f"https://mtgtop8.com/event{href}"
        }
        decks.append(deck)
    return decks

  @classmethod
  async def get_deck_page(
      cls,
      deck_url: str,
  ) -> str:
    """Fetches the text of the HTMl on a page for a specific deck.

    Args:
      deck_url: the full url of the deck on mtgtop8.com
    Returns:
      A string with the HTML of the page
    """
    response = await HttpClient.HTTP_SESSION.get(url=deck_url)
    response_text = await response.text()
    return response_text

  @classmethod
  async def get_last_tournament(
      cls,
      text: str,
  ) -> str:
    """Fetches the latest tournament held on a mtgtop8 format page.

    Args:
      text: html text of the mtgtop8 format page
    Returns:
      A string with the link to a tournamnet
    """
    soup = BeautifulSoup(text, 'html.parser')
    tables = soup.find_all('table', class_='Stable')
    table = tables[1]
    first_a_tag = table.find("a")
    href = first_a_tag["href"]
    return href

  @classmethod
  async def get_deck_list(
      cls,
      text: str,
  ) -> tuple:
    """Parses the cards on a deck page and composes into a list and dict.

    Args:
      text: html text of the mtgtop8 deck page
    Returns:
      A tuple with a full list of cards as element 0 and a dict as element 1
    """
    decklist = []
    decklist_dict = {}
    soup = BeautifulSoup(text, 'html.parser')
    cards = soup.find_all('div', class_='deck_line hover_tr')
    for card in cards:
      card_number = int(card.contents[0].strip())
      card_name = card.find('span', class_='L14').text.strip()
      for _ in range(card_number):
        decklist.append(card_name)
      decklist_dict[card_name] = card_number
    return (decklist, decklist_dict)

  @classmethod
  async def generate_random_hand(
      cls,
      format: Formats,
  ) -> list[str]:
    """Generates a random starting hand for a deck from the chosen format.

    Args:
      format: a format to generate a hand for
    Returns:
      A list with 7 cards
    """
    format_text =  await cls.get_format_page(format=format)
    tournament = await cls.get_last_major_tournament(text=format_text)
    decks = await cls.get_decks_from_tournament_page(tournament_link=tournament)
    rand_number = random.randint(0, 3)
    deck = decks[rand_number]
    deck_name = deck.get("name")
    deck_link = deck.get("link")
    deck_text = await cls.get_deck_page(deck_url=deck_link)
    decklist_tuple = await cls.get_deck_list(text=deck_text)
    decklist = decklist_tuple[0]
    random.shuffle(decklist)
    sample_hand = decklist[:7]
    sample_hand.sort()
    text = f"Deck: {deck_name}\nHand:\n"
    for card in sample_hand:
      text += f"{card}\n"
    return sample_hand
