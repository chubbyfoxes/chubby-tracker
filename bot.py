
import discord
import asyncio
import aiohttp
from sales_listener import check_sales
from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
RONIN_API_URL = os.getenv("RONIN_API_URL")
OPENSEA_API_URL = "https://api.opensea.io/api/v2/events"
OPENSEA_API_KEY = os.getenv("OPENSEA_API_KEY")
POLL_INTERVAL_SECONDS = 10
FETCH_SIZE = 9

# Lista de colecciones a trackear
COLLECTIONS = [
    # OpenSea
    {
        "name": "Chubby Foxes",
        "contract": "0xd39c8d7e107db9a85896eb78e652496977b7f674",
        "slug": "chubby-foxes",
        "market": "opensea",
        "last_timestamp": 0
    },

    # Ronin (usando mismos contratos que OpenSea)
    {
        "name": "Chubby Foxes",
        "contract": "0xd39c8d7e107db9a85896eb78e652496977b7f674",
        "market": "ronin",
        "last_timestamp": 0
    }
]


class NFTSalesBot(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = None
        self.channel = None
        self.seen_tx_hashes = set()
        self.running = True
        self.bg_task = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        self.bg_task = asyncio.create_task(self._poll_sales())

    async def on_ready(self):
        print(f"Connected as {self.user}")
        self.channel = self.get_channel(CHANNEL_ID)
        if not self.channel:
            print(f"Channel {CHANNEL_ID} not found")
            await self.close()
            return
        await self.channel.send("✅ Bot started")

    async def _poll_sales(self):
        await self.wait_until_ready()
        while not self.is_closed() and self.running:
            try:
                for collection in COLLECTIONS:
                    api_url = (
                        RONIN_API_URL
                        if collection["market"] == "ronin"
                        else f"{OPENSEA_API_URL}?collection_slug={collection['slug']}"
                    )
                    api_key = API_KEY if collection["market"] == "ronin" else OPENSEA_API_KEY
                    new_ts = await check_sales(
                        self.session,
                        self.channel,
                        api_url,
                        api_key,
                        collection["last_timestamp"],
                        collection["name"],
                        collection["contract"] if collection["market"] == "ronin" else collection["slug"],
                        FETCH_SIZE,
                        self.seen_tx_hashes,
                        collection["market"]
                    )
                    if new_ts > collection["last_timestamp"]:
                        collection["last_timestamp"] = new_ts
            except Exception as e:
                print(f"Polling error: {e}")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def close(self):
        self.running = False
        if self.bg_task:
            self.bg_task.cancel()
        if self.session:
            await self.session.close()
        await super().close()

intents = discord.Intents.default()
client = NFTSalesBot(intents=intents)
client.run(DISCORD_TOKEN)
