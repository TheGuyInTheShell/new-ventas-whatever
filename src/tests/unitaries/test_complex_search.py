import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"


async def test_complex_search():
    # Nota: Este test asume que el servidor uvicorn está corriendo
    # y que los permisos están configurados o se saltan en modo desarrollo.
    
    # Prefix based on main.py auto_router_api: /api/v1 + folder name (business_entities)
    # The old tests used /api/business-entities-search-by, but the current structure suggests:
    API_PREFIX = "/api/v1/business_entities"

    async with httpx.AsyncClient() as client:
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


if __name__ == "__main__":
    asyncio.run(test_complex_search())
