import os
import requests

NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")  # Put your integration token in .env

class NotionHelper:
    def __init__(self):
        self.base_url = "https://api.notion.com/v1/"
        self.token = NOTION_API_TOKEN

    def fetch_contacts(self):
        # --- Replace with your Notion database ID ---
        database_id = os.getenv("NOTION_CONTACTS_DATABASE_ID", "YOUR_DATABASE_ID")
        url = f"{self.base_url}databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.post(url, headers=headers, json={})
            resp.raise_for_status()
            results = resp.json().get("results", [])
            # Parse results as needed, e.g.:
            contacts = []
            for page in results:
                properties = page.get("properties", {})
                contact = {
                    "id": page.get("id"),
                    "name": properties.get("Name", {}).get("title", [{}])[0].get("plain_text", ""),
                    "email": properties.get("Email", {}).get("email", ""),
                }
                contacts.append(contact)
            return contacts
        except Exception as e:
            print("Notion fetch error:", e)
            return []
