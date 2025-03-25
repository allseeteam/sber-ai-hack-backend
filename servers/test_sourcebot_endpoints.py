import httpx
import json
import asyncio
from rich import print


async def test_endpoints():
    async with httpx.AsyncClient() as client:
        try:
            # Test version endpoint
            print("[bold blue]=== Testing Version Endpoint ===[/bold blue]")
            version = await client.get("http://localhost:3000/api/version")
            print("Status:", version.status_code)
            print("Response:", json.dumps(version.json(), indent=2))
            print()

            # Test repos endpoint
            print("[bold blue]=== Testing Repos Endpoint ===[/bold blue]")
            repos = await client.get("http://localhost:3000/api/repos")
            print("Status:", repos.status_code)
            print("Response:", json.dumps(repos.json(), indent=2))
            print()

            # Test search endpoint
            print("[bold blue]=== Testing Search Endpoint ===[/bold blue]")
            search = await client.post(
                "http://localhost:3000/api/search",
                json={"query": "tensor", "maxMatchDisplayCount": 5},
            )
            print("Status:", search.status_code)
            print("Response keys:", json.dumps(list(search.json().keys()), indent=2))
            print("\nFull Response:", json.dumps(search.json(), indent=2))

        except Exception as e:
            print(f"[bold red]Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
