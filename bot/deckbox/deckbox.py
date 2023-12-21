"""Module for scraping deckbox website
"""
import base64
import ssl
import csv
from io import StringIO
from bot.config import config
from bot.config.urls import (
    DECKBOX_LOGIN_AUTHENTICATE_URL,
    DECKBOX_LOGIN_GET_TOKEN_URL,
    DECKBOX_SCV_EXPORT_URL,
    DECKBOX_TRADELIST_CARDNAME_FILTER_URL,
    DECKBOX_USER_URL,
)
from bot.config.http_client import HttpClient
from bs4 import BeautifulSoup
from datetime import datetime

class Deckbox:

  @classmethod
  async def convert_to_base64(cls, value: str) -> str:
    """Converts string to base64.

    Args:
      value: value of the string
    Returns:
      A converted string
    """
    encoded_bytes = value.encode("utf-8")
    base64_bytes = base64.b64encode(encoded_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string

  @classmethod
  async def create_deckbox_url(
      cls,
      deckbox_id: str,
      card_name: str,
  ) -> str:
    """Generates a URL for the deckbox filtered by cardname.

    Args:
      deckbox_id: id of the deckbox for the url
      card_name: name of the card to filter by
    Returns:
      A string with the URL
    """
    converted_name = await cls.convert_to_base64(value=card_name)
    url = DECKBOX_TRADELIST_CARDNAME_FILTER_URL.format(
        deckbox_id=deckbox_id,
        card_name=converted_name,
    )
    return url

  @classmethod
  async def create_deckbox_user_url(
      cls,
      username: str,
  ) -> str:
    """Generates a URL for the deckbox user.

    Args:
      username: name of the user
    Returns:
      A string with the URL
    """
    return DECKBOX_USER_URL.format(username=username)

  @classmethod
  async def login(cls) -> bool:
    """Logs into the deckbox site and saves the cookie to the config.

    Returns:
      True if login was successful, False if not
    """
    resp = await HttpClient.HTTP_SESSION.get(url=DECKBOX_LOGIN_GET_TOKEN_URL)
    response_text = await resp.text()
    response_cookies = resp.cookies
    soup = BeautifulSoup(response_text, "html.parser")
    auth_input = soup.find("input", {"name": "authenticity_token"})
    if auth_input and "_tcg_session" in response_cookies:
      session_token = response_cookies["_tcg_session"].value
      headers = {"Cookie": f"_tcg_session={session_token};"}
      token = auth_input.get("value")
      auth_response = await HttpClient.HTTP_SESSION.post(
          url=DECKBOX_LOGIN_AUTHENTICATE_URL.format(
              token=token,
              login=config.DECKBOX_LOGIN,
              password=config.DECKBOX_PASSWORD,
          ),
          headers=headers,
      )
      if "_tcg_session" in auth_response.cookies:
        config.DECKBOX_COOKIE = auth_response.cookies["_tcg_session"].value
      else:
        return False
      now = datetime.now()
      datetime_string = now.strftime("%Y-%m-%d %H:%M:%S")
      config.DECKBOX_COOKIE_LAST_LOGIN = datetime_string
      return True
    else:
      return False

  @classmethod
  async def check_cookie(cls) -> bool:
    """Checks if deckbox cookie exists and is less than 60 minutes old. If the
    cookie doesn't exist or is old authenticates on the deckbox website and
    saves a cookie with the session to the config.

    Returns:
      True if up-to-date cookie is in config file, False if not
    """
    string_cookie = config.DECKBOX_COOKIE
    if string_cookie == "":
      await cls.login()
    string_date = config.DECKBOX_COOKIE_LAST_LOGIN
    if string_date == "":
      return False
    saved_date = datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    time_difference = now - saved_date
    minutes_passed = round(time_difference.total_seconds() / 60, 2)
    old_cookie = config.DECKBOX_COOKIE
    if minutes_passed > 60:
      print("The deckbox cookie is expired! Trying to relog!")
      await cls.login()
      return config.DECKBOX_COOKIE != old_cookie
    else:
      return config.DECKBOX_COOKIE != ""

  @classmethod
  async def get_deckbox_ids_from_account(
      cls,
      account_name: str,
  ) -> dict:
    """Fetches IDs of deckbox wishlist and tradelist for a given account name.

    Args:
      account_name: name of the account to fetch lists from
    Returns:
      A dict with keys "success", "tradelist", "wishlist"
    """
    result = {
        "success": False,
        "tradelist": "",
        "wishlist": "",
    }
    logged_in = await cls.check_cookie()
    if not logged_in:
      return result
    user_url = DECKBOX_USER_URL.format(username=account_name)
    headers = {
      "Cookie": f"_tcg_session={config.DECKBOX_COOKIE};"
    }
    response = await HttpClient.HTTP_SESSION.get(
        url=user_url,
        ssl=ssl.SSLContext(ssl.PROTOCOL_TLSv1_2),
        headers=headers,
    )
    text = await response.text()
    valid_user = await cls.check_deckbox_validity(text=text)
    if not valid_user:
      return result
    soup = BeautifulSoup(text, 'html.parser')
    ul_element = soup.find('ul', {'id': 'section_mtg', 'class': 'submenu'})
    if ul_element:
      li_elements = ul_element.find_all('li', class_='submenu_entry')
      # Extract href from the last two <li> elements
      sets = [li.find('a').get('href') for li in li_elements[1:3]]
      result["tradelist"] = sets[0][6:]
      result["wishlist"] = sets[1][6:]
      result["success"] = True
    return result

  @classmethod
  async def check_deckbox_validity(
      cls,
      text: str,
  ) -> bool:
    """Checks if a deckbox with a given username exists.

    Args:
      text: html text of the deckbox user page
    Returns:
      A boolean that shows if the deckbox username is valid
    """
    soup = BeautifulSoup(text, 'html.parser')
    content_div = soup.find('div', id='content')
    user_exists = False
    if content_div:
      section_title_div = content_div.find('div', class_='section_title')
    if section_title_div:
      user_exists = True
    return user_exists

  @classmethod
  async def cache_deckbox_list(
      cls,
      deckbox: str,
      account_name: str,
  ) -> dict:
    """Caches deckbox wishlist/tradelist into the corresponding collection.

    Args:
      deckbox: id of the deckbox
      account_name: name of the account deckbox belongs to
    Returns:
      A dict with the object for saving deckbox to the DB
    """
    logged_in = await cls.check_cookie()
    if not logged_in:
      return (False, "Problem with login into deckbox.org")
    full_url = DECKBOX_SCV_EXPORT_URL.format(deckbox_id=deckbox)
    headers = {
      "Cookie": f"_tcg_session={config.DECKBOX_COOKIE};"
    }
    response = await HttpClient.HTTP_SESSION.get(
        url=full_url,
        ssl=ssl.SSLContext(ssl.PROTOCOL_TLSv1_2),
        headers=headers,
    )
    received_csv = await response.text()
    csv_object = StringIO(received_csv)
    reader = csv.DictReader(csv_object)
    data = list(reader)
    now = datetime.now()
    datetime_string = now.strftime("%Y-%m-%d %H:%M:%S")
    resulting_object = {
        "account_name": account_name.lower(),
        "deckbox_id": deckbox,
        "last_cached": datetime_string,
        "cards": {},
    }
    for line in data:
      card_name = line.get("Name").lower()
      card_count = int(line.get("Count"))
      if card_name in resulting_object["cards"]:
        resulting_object["cards"][card_name] += card_count
      else:
        resulting_object["cards"][card_name] = card_count
    return resulting_object
