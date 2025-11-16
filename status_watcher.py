import aiohttp
import asyncio
import hashlib
import json
from datetime import datetime

STATUS_URL = "https://status.openai.com/api/v2/summary.json"

class StatusWatcher:
    """
       ETag (If-None-Match)
       Last-Modified (If-Modified-Since)
       Hash fallback if headers missing
    """

    def __init__(self):
        self.etag = None
        self.last_modified = None
        self.last_hash = None
        self.interval = 30  

    async def fetch_summary(self, session):
        headers = {}
        if self.etag:
            headers["If-None-Match"] = self.etag
        elif self.last_modified:
            headers["If-Modified-Since"] = self.last_modified

        async with session.get(STATUS_URL, headers=headers) as resp:
            
            if resp.status == 304:
                return None

           
            if resp.status != 200:
                print("Status page returned:", resp.status)
                return None

            # Store validators
            self.etag = resp.headers.get("ETag")
            self.last_modified = resp.headers.get("Last-Modified")
            return await resp.json()

    def compute_hash(self, data):
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    async def start(self):
        async with aiohttp.ClientSession() as session:
            print("Monitoring OpenAI Status Page...\n")

            while True:
                data = await self.fetch_summary(session)

                # No-change from server
                if data is None:
                    await asyncio.sleep(self.interval)
                    continue

                # Hash fallback detection
                new_hash = self.compute_hash(data)
                if self.last_hash and new_hash == self.last_hash:
                    await asyncio.sleep(self.interval)
                    continue

                self.last_hash = new_hash
                self.process(data)

                # Adaptive polling (faster on updates, slower when stable)
                self.interval = max(20, self.interval * 0.5)

                await asyncio.sleep(self.interval)

    def process(self, summary):
        """
        Extract incidents / component updates and print them.
        Interview-friendly simplification: Only focuses on real incidents.
        """
        incidents = summary.get("incidents", [])
        components = summary.get("components", [])

        # Print active incidents
        for inc in incidents:
            if inc["status"] not in ("resolved", "postmortem"):
                name = inc["name"]
                updates = inc.get("incident_updates", [])
                message = (updates[0]["body"] if updates else inc["status"]).strip()
                self.print_event(name, message)

        # Print degraded components
        for comp in components:
            if comp["status"] != "operational":
                self.print_event(
                    comp["name"],
                    f"Component {comp['name']} is {comp['status']}"
                )

    def print_event(self, product, message):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Product: {product}")
        print(f"Status: {message}")
        print("-" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(StatusWatcher().start())
    except KeyboardInterrupt:
        print("\nStopped.")
