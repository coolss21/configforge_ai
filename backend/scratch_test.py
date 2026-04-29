import httpx, asyncio

async def test():
    print("Testing connection with key: sk-or-v1-8fbc...d4fb")
    async with httpx.AsyncClient() as client:
        r2 = await client.post(
            'http://localhost:8002/generate',
            json={'prompt': 'Build a very simple todo app', 'mode': 'fast'},
            headers={'Origin': 'http://localhost:3000'},
            timeout=120.0
        )
        print('STATUS:', r2.status_code)
        if r2.status_code == 200:
            print("SUCCESS! Pipeline completed.")
        else:
            print("ERROR:", r2.text[:200])

asyncio.run(test())
