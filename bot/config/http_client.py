"""Module for initializing and closing the HTTP client sessions.
"""
import aiohttp

class HttpClient:
  HTTP_SESSION = None

  @classmethod
  async def init_client(cls):
    """Initializes the new Http client session.
    """
    # Initialize the ClientSession
    cls.HTTP_SESSION = aiohttp.ClientSession()

  @classmethod
  async def close_client(cls):
    """Closes the existing Http client session.
    """
    # Close the ClientSession
    await cls.HTTP_SESSION.close()
