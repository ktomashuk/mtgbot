"""URLS used by other modules.
"""

SCRYFALL_GET_CARD_URL = "https://api.scryfall.com/cards/named?fuzzy={name}"
SCRYFALL_GET_RANDOM_CARD_URL = "https://api.scryfall.com/cards/random"
DECKBOX_TRADELIST_URL = "https://deckbox.org/sets/{deckbox_id}"
DECKBOX_TRADELIST_CARDNAME_FILTER_URL = (
  "https://deckbox.org/sets/{deckbox_id}?f=17{card_name}"
)
DECKBOX_SCV_EXPORT_URL = (
  "https://deckbox.org/sets/export/{deckbox_id}?format=csv&f=&s=&o=&columns="
)
DECKBOX_LOGIN_AUTHENTICATE_URL = (
  "https://deckbox.org/accounts/login?authenticity_token={token}&return_to=%2F&login={login}&password={password}&remember_me=on"
)
DECKBOX_LOGIN_GET_TOKEN_URL = "https://deckbox.org/accounts/login"
DECKBOX_USER_URL = "https://deckbox.org/users/{username}"
MYTHICCARD_CARD_URL = (
  "https://mythiccard.com/index.php?route=product/search&search={card_name}&fq=1"
)
MYTHICCARD_ALL_CARDS_URL = (
  "https://mythiccard.com/index.php?route=product/category&path=66&limit=100&fq=1&page={page}"
)
MTGTOP8_PAUPER_FORMAT_URL = (
  "https://mtgtop8.com/format?f=PAU"
)
MTGTOP8_MODERN_FORMAT_URL = (
  "https://mtgtop8.com/format?f=MO"
)
