"""A module for scraping the mythiccard.com site.
"""
from bot.config.urls import MYTHICCARD_ALL_CARDS_URL
from bot.config.http_client import HttpClient
from bot.utils.utils import Utils
from bs4 import BeautifulSoup

class MythicCard:

  @classmethod
  async def get_all_cards(cls) -> dict:
    """Fetches all the cards from mythiccard site.

    Returns:
      A dict with all the cards
    """
    page = 1
    full_card_dicts = []
    active = True
    while active:
      print(f"Fetching page {page}")
      card_response = await cls.get_cards_page(page=page)
      cards_dict = await cls.get_cards_on_page(text=card_response)
      if not cards_dict:
        print("LAST PAGE")
        active = False
      full_card_dicts.append(cards_dict)
      page += 1
    full_dict = await Utils.construct_united_mythic_cards_dict(
        input_dicts=full_card_dicts,
    )
    return full_dict

  @classmethod
  async def get_cards_page(cls, page: int) -> str:
    """Fetches the text of the HTMl on a page with a given number.

    Args:
      page: number of the page
    Returns:
      A string with the HTML of the page
    """
    url = MYTHICCARD_ALL_CARDS_URL.format(page=page)
    response = await HttpClient.HTTP_SESSION.get(url=url)
    response_text = await response.text()
    return response_text

  @classmethod
  async def get_cards_on_page(
      cls,
      text: str,
  ) -> dict:
    """Parses the cards on a mythiccard page and adds them to a dict.

    Args:
      text: html text of the mythiccard user page
    Returns:
      A dict with parse results
    """
    soup = BeautifulSoup(text, 'html.parser')
    products_dict = {}
    products = soup.find('div', class_='main-products product-grid')
    if not products:
      return products_dict
    layout = products.find_all('div', class_='product-layout')
    for product_div in layout:
      # Extract the name
      name_div = product_div.find('div', class_='name')
      if name_div and name_div.find('a'):
        name = name_div.get_text(strip=True)
        url = name_div.find('a')['href']
      else:
          name = 'No Name'
          url = 'No URL'
      # Extract stock count
      stock_span = product_div.find('span', class_='stat-2')
      if stock_span:
        stock_count = int(stock_span.find_all('span')[-1].get_text(strip=True))
      else:
        stock_count = 0
      # Extract price
      price_span = product_div.find('span', class_='price-normal')
      price = price_span.get_text(strip=True) if price_span else 'No Price'
      # Add to dictionary
      lower_name = name.lower()
      if not products_dict.get(lower_name):
        products_dict[lower_name] = [
            {'count': stock_count, 'price': price, "url": url}
        ]
      else:
        products_dict[lower_name].append(
            {'count': stock_count, 'price': price, "url": url}
        )
    return products_dict
