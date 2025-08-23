import asyncio
import aiohttp
import json

# === CONFIG ===
API_URL = "https://realtime.oxylabs.io/v1/queries"
AUTH = aiohttp.BasicAuth("username", "password")  # <-- replace with your credentials
LIMIT = 6  # max concurrent requests


async def fetch_and_save(session: aiohttp.ClientSession, sku: str, query: str, sem: asyncio.Semaphore):
    payload = {
        "source": "google_shopping_search",
        "domain": "com.br",
        "query": query,
        "pages": 1,
        "parse": True,
        "context": [
            {"key": "nfpr", "value": "true"},
        ],
    }

    async with sem:  # limit concurrency
        try:
            async with session.post(API_URL, auth=AUTH, json=payload) as resp:
                data = await resp.json()
        except Exception as e:
            print(f"[ERROR] Request failed for {sku}: {e}")
            return

        # Save JSON response to file
        filename = f"{sku}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[OK] Saved response for {sku} → {filename}")
        except Exception as e:
            print(f"[ERROR] Could not save {sku}: {e}")


async def main():
    user_input = input("Enter sku//query pairs (format: sku1//query1;sku2//query2;...):\n").strip()

    if not user_input:
        print("No input provided.")
        return

    pairs = [p for p in user_input.split(";") if "//" in p]

    sem = asyncio.Semaphore(LIMIT)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for pair in pairs:
            sku, query = pair.split("//", 1)
            tasks.append(fetch_and_save(session, sku.strip(), query.strip(), sem))

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
