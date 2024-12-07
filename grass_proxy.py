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
    def __init__(self, socks5_proxy, user_id):
        self.socks5_proxy = socks5_proxy
        self.user_id = user_id
        self.device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
        self.user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome').random
        self.uri_list = [
            "wss://proxy2.wynd.network:4444/",
            "wss://proxy2.wynd.network:4650/"
        ]
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def connect(self):
        logger.info(f"Device ID: {self.device_id}")
        while True:
            try:
                await asyncio.sleep(random.uniform(0.1, 1.0))
                uri = random.choice(self.uri_list)
                proxy = Proxy.from_url(self.socks5_proxy)
                headers = {"User-Agent": self.user_agent}

                async with proxy_connect(
                    uri, proxy=proxy, ssl=self.ssl_context,
                    server_hostname="proxy2.wynd.network",
                    extra_headers=headers
                ) as websocket:
                    await self.handle_websocket(websocket)
            except Exception as e:
                logger.error(f"Error with proxy {self.socks5_proxy}: {e}")

    async def handle_websocket(self, websocket):
        asyncio.create_task(self.send_ping(websocket))

        while True:
            response = await websocket.recv()
            message = json.loads(response)
            logger.info(f"Received message: {message}")
            await self.process_message(websocket, message)

    async def send_ping(self, websocket):
        while True:
            ping_message = json.dumps({
                "id": str(uuid.uuid4()),
                "version": "1.0.0",
                "action": "PING",
                "data": {}
            })
            logger.debug(f"Sending ping: {ping_message}")
            await websocket.send(ping_message)
            await asyncio.sleep(5)

    async def process_message(self, websocket, message):
        action = message.get("action")
        if action == "AUTH":
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
            logger.debug(f"Sending auth response: {auth_response}")
            await websocket.send(json.dumps(auth_response))
        elif action == "PONG":
            pong_response = {"id": message["id"], "origin_action": "PONG"}
            logger.debug(f"Sending pong response: {pong_response}")
            await websocket.send(json.dumps(pong_response))


class ProxyManager:
    def load_file(file_name, data_type):
        try:
            with open(file_name, 'r') as file:
                data = file.read().splitlines()
                if not data:
                    logger.error(f"No {data_type} found in '{file_name}'.")
                    return []
                logger.info(f"{data_type.capitalize()} read from file: {data}")
                return data
        except FileNotFoundError:
            logger.error(f"Error: '{file_name}' file not found.")
            return []

    async def run(self):
        user_ids = self.load_file('user_id.txt', 'user IDs')
        proxies = self.load_file('local_proxies.txt', 'proxies')

        if not user_ids or not proxies:
            return

        tasks = [
            WebSocketClient(proxy, user_id).connect()
            for proxy in proxies for user_id in user_ids
        ]
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    proxy_manager = ProxyManager()
    asyncio.run(proxy_manager.run())
