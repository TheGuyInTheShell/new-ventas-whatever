import asyncio
import httpx
import json
import pytest

BASE_URL = "http://localhost:8000"


@pytest.fixture
def anyio_backend():
    """Restrict anyio to asyncio only — trio is not installed/compatible."""
    return 'asyncio'


@pytest.mark.anyio
async def test_complex_search():
    # NOTE: This is an integration smoke test.
    # It requires the uvicorn dev server to be running at localhost:8000.
    # Skipped automatically when the server is unreachable.
    API_PREFIX = "/api/v1/business_entities"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            print(f"--- Testing Specialized Search by Name (Endpoint: {API_PREFIX}/search) ---")
            # Schema: RQBusinessEntitySearch (requires name)
            payload = {"name": "chinese-restaurant", "hierarchy": True, "groups": True}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/search", json=payload
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Total found: {data['total']}")
                for item in data["data"]:
                    print(f" - {item['name']} (Groups: {item['groups']})")
                    if item.get("children"):
                        print(f"   - Children found: {len(item['children'])}")
            else:
                print(f"Error: {response.text}")

            print(f"\n--- Testing Specialized Search by Child (Endpoint: {API_PREFIX}/search/child) ---")
            # Schema: RQBusinessEntitySearchChild (requires name, child_name)
            payload = {"name": "chinese-restaurant", "child_name": "inventory"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/search/child", json=payload
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Results: {data['total']}")
                for item in data["data"]:
                    child = item.get("child")
                    print(f" - Parent: {item['name']} -> Child Matched: {child['name'] if child else 'None'}")
            else:
                print(f"Error: {response.text}")

            print(f"\n--- Testing Specialized Search by Groups (Endpoint: {API_PREFIX}/search/groups) ---")
            # Schema: RQBusinessEntitySearchGroups (requires name, group_names)
            payload = {"name": "chinese-restaurant", "group_names": ["admin", "pos"]}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/search/groups", json=payload
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Entities found in groups: {data['total']}")
                for item in data["data"]:
                    print(f" - {item['name']} (Groups: {item['groups']})")
            else:
                print(f"Error: {response.text}")

            print(f"\n--- Testing Generic Advanced Search (Endpoint: {API_PREFIX}/search_by) ---")
            # Schema: RQBusinessEntitiesSearch (original generic schema)
            payload = {"name": "chinese-restaurant", "groups": True, "page_size": 5}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/search_by", json=payload
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Advanced search results: {data['total']}")
            else:
                print(f"Error: {response.text}")
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        pytest.skip(f"Dev server is unreachable at {BASE_URL}. Skipping integration smoke test: {e}")


if __name__ == "__main__":
    asyncio.run(test_complex_search())

