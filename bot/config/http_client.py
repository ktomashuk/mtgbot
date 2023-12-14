import aiohttp

class HttpClient:
  HTTP_SESSION = None

  @classmethod
  async def init_client(cls):
    # Initialize the ClientSession
    cls.HTTP_SESSION = aiohttp.ClientSession()

  @classmethod
  async def close_client(cls):
    # Close the ClientSession
    await cls.HTTP_SESSION.close()
