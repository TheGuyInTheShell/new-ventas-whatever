import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_complex_search():
    # Nota: Este test asume que el servidor uvicorn está corriendo
    # y que los permisos están configurados o se saltan en modo desarrollo.
    
    async with httpx.AsyncClient() as client:
        print("--- Testing Search by Name (partial 'chinese') ---")
        payload = {
            "name": "chinese",
            "page": 1,
            "page_size": 10
        }
        response = await client.post(f"{BASE_URL}/api/business-entities-search-by/search", json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total found: {data['total']}")
            for item in data['data']:
                print(f" - {item['name']} (Groups: {item['groups']})")
        else:
            print(f"Error: {response.text}")

        print("\n--- Testing Search by Parent ID (find children of 'chinese-restaurant') ---")
        # Primero buscamos el ID de chinese-restaurant
        res_id = await client.post(f"{BASE_URL}/api/business-entities-search-by/search", json={"name": "chinese-restaurant"})
        if res_id.status_code == 200 and res_id.json()['data']:
            parent_id = res_id.json()['data'][0]['id']
            print(f"Parent ID (chinese-restaurant): {parent_id}")
            
            payload = {
                "parent_id": parent_id,
                "page": 1,
                "page_size": 10
            }
            response = await client.post(f"{BASE_URL}/api/business-entities-search-by/search", json=payload)
            if response.status_code == 200:
                data = response.json()
                print(f"Children found: {data['total']}")
                for item in data['data']:
                    print(f" - {item['name']}")
        
        print("\n--- Testing Search with Groups (partial 'admin') ---")
        payload = {
            "group_name": "admin",
            "page": 1,
            "page_size": 10
        }
        response = await client.post(f"{BASE_URL}/api/business-entities-search-by/search", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Entities in 'admin' groups: {data['total']}")
            for item in data['data']:
                print(f" - {item['name']} (Groups: {item['groups']})")

if __name__ == "__main__":
    asyncio.run(test_complex_search())
