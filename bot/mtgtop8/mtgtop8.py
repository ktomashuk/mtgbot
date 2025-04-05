"""A module for scraping the mtgtop8.com site.
"""
import random
from bot.config.urls import (
    MTGTOP8_PAUPER_FORMAT_URL,
    MTGTOP8_MODERN_FORMAT_URL
)
from bot.scryfall.scryfall import ScryfallFetcher
from bot.config.http_client import HttpClient
from bs4 import BeautifulSoup
from enum import Enum
import aiohttp
import asyncio
from PIL import Image
from io import BytesIO


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
    sideboard_header = soup.find("div", string="SIDEBOARD")
    sideboard_container = sideboard_header.find_parent("div", style=lambda x: x and "margin" in x)
    all_deck_lines = soup.find_all("div", class_="deck_line hover_tr")
    non_sideboard_deck_lines = [
        div for div in all_deck_lines
        if not sideboard_container and True or not sideboard_container in div.parents
    ]
    for card_div in non_sideboard_deck_lines:
      card_number = int(card_div.contents[0].strip())
      card_name = card_div.find('span', class_='L14').text.strip()
      for _ in range(card_number):
        decklist.append(card_name)
      decklist_dict[card_name] = card_number
    return (decklist, decklist_dict)

  @classmethod
  async def fetch_image(
      cls,
      image_url: str,
  ) -> Image.Image:
    """Generates a random starting hand for a deck from the chosen format.

    Args:
      format: a format to generate a hand for
    Returns:
      A list with 7 cards
    """
    async with HttpClient.HTTP_SESSION.get(image_url) as response:
      if response.status == 200:
        img_data = await response.read()
        print(f"Downloaded {image_url} ({len(img_data)} bytes)")
        return Image.open(BytesIO(img_data)).convert("RGBA")
      else:
        print(f"Failed to download {image_url} (Status: {response.status})")
        return None

  @classmethod
  async def generate_hand_image(
      cls,
      image_urls: list[str],
  ) -> list[str]:
    """Generates a random starting hand for a deck from the chosen format.

    Args:
      format: a format to generate a hand for
    Returns:
      A list with 7 cards
    """
    images = await asyncio.gather(*[cls.fetch_image(url) for url in image_urls])
    images = [img for img in images if img is not None]
    print(f"Fetched {len(images)} images")
    overlap_percent = 0.25
    card_width = images[0].width
    card_height = images[0].height
    step = int(card_width * (1 - overlap_percent))

    width = card_width + step * (len(images) - 1)
    height = card_height

    # Create a blank image with transparency
    final_image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    # Paste images with overlap
    x_offset = 0
    for img in images:
        final_image.paste(img, (x_offset, 0), img)
        x_offset += step
    print(f"Final image size: {final_image.size}")
    # Save or show the final image
    url = await cls.upload_to_catbox(final_image)
    return url

  @classmethod
  async def upload_to_catbox(cls, image: Image.Image) -> str:
    """Uploads a PIL image to catbox.moe and returns the direct URL."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    data = aiohttp.FormData()
    data.add_field('reqtype', 'fileupload')
    data.add_field('fileToUpload', buffer, filename='collage.png', content_type='image/png')
    print("Trying to upload catbox.moe...")
    async with HttpClient.HTTP_SESSION.post("https://catbox.moe/user/api.php", data=data) as resp:
      if resp.status == 200:
        url = await resp.text()
        print("Uploaded to:", url)
        return url.strip()
      else:
        raise Exception(f"Failed to upload image (Status: {resp.status})")

  @classmethod
  async def generate_random_hand(
      cls,
      format: Formats = Formats.PAUPER,
  ) -> list[str]:
    """Generates a random starting hand for a deck from the chosen format.

    Args:
      format: a format to generate a hand for
    Returns:
      A list with 7 cards
    """
    format_text =  await cls.get_format_page(format=format)
    tournament = await cls.get_last_tournament(text=format_text)
    decks = await cls.get_decks_from_tournament_page(tournament_link=tournament)
    decks_len = len(decks)
    rand_number = random.randint(0, decks_len - 1)
    deck = decks[rand_number]
    deck_name = deck.get("name")
    deck_link = deck.get("link")
    deck_text = await cls.get_deck_page(deck_url=deck_link)
    decklist_tuple = await cls.get_deck_list(text=deck_text)
    decklist = decklist_tuple[0]
    random.shuffle(decklist)
    sample_hand = decklist[:7]
    sample_hand.sort()
    card_urls = []
    for card in sample_hand:
      card_url = await ScryfallFetcher.get_card_image(card_name=card)
      if isinstance(card_url, list):
        card_url = card_url[0]
      card_urls.append(card_url)
    image_url = await cls.generate_hand_image(image_urls=card_urls)
    return (image_url, deck_name)
