import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent

class WebSocketClient:
    def __init__(self, proxy_url, user_id):
        self.proxy_url = proxy_url
        self.user_id = user_id
        self.device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, proxy_url))
        self.user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome').random
        self.server_hostname = "proxy2.wynd.network"
        self.uris = [
            "wss://proxy2.wynd.network:4444/",
            "wss://proxy2.wynd.network:4650/"
        ]
        self.ssl_context = self._create_ssl_context()

    def _create_ssl_context(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    async def _send_ping(self, websocket):
        while True:
            ping_message = {
                "id": str(uuid.uuid4()),
                "version": "1.0.0",
                "action": "PING",
                "data": {}
            }
            await websocket.send(json.dumps(ping_message))
            logger.debug(f"Ping sent: {ping_message}")
            await asyncio.sleep(5)

    async def _handle_message(self, websocket):
        while True:
            try:
                response = await websocket.recv()
                message = json.loads(response)
                logger.info(f"Message received: {message}")

                if message.get("action") == "AUTH":
                    auth_response = {
                        "id": message["id"],
                        "origin_action": "AUTH",
                        "result": {
                            "browser_id": self.device_id,
                            "user_id": self.user_id,
                            "user_agent": self.user_agent,
                            "timestamp": int(time.time()),
                            "device_type": "desktop",
                            "version": "4.28.2",
                        }
                    }
                    await websocket.send(json.dumps(auth_response))
                    logger.debug(f"Auth response sent: {auth_response}")

                elif message.get("action") == "PONG":
                    pong_response = {"id": message["id"], "origin_action": "PONG"}
                    await websocket.send(json.dumps(pong_response))
                    logger.debug(f"Pong response sent: {pong_response}")

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                break

    async def connect(self):
        proxy = Proxy.from_url(self.proxy_url)
        uri = random.choice(self.uris)
        headers = {"User-Agent": self.user_agent}

        while True:
            try:
                await asyncio.sleep(random.uniform(0.1, 1))
                async with proxy_connect(
                    uri, 
                    proxy=proxy, 
                    ssl=self.ssl_context,
                    server_hostname=self.server_hostname, 
                    extra_headers=headers
                ) as websocket:
                    logger.info(f"Connected to {uri} via {self.proxy_url}")
                    asyncio.create_task(self._send_ping(websocket))
                    await self._handle_message(websocket)
            except Exception as e:
                logger.error(f"Connection error with proxy {self.proxy_url}: {e}")
                await asyncio.sleep(5)

async def read_file(file_path, error_message):
    try:
        with open(file_path, 'r') as file:
            data = file.read().splitlines()
            if not data:
                logger.error(f"No data found in {file_path}")
            return data
    except FileNotFoundError:
        logger.error(error_message)
        return []

async def main():
    user_ids = await read_file('user_id.txt', "Error: 'user_id.txt' not found.")
    if not user_ids:
        return

    proxies = await read_file('local_proxies.txt', "Error: 'local_proxies.txt' not found.")
    if not proxies:
        return

    tasks = [WebSocketClient(proxy, user_id).connect() for proxy in proxies for user_id in user_ids]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
