# services/supabase_service.py

from supabase import create_client, Client, ClientOptions
import random

class SupabaseClient:
    def __init__(self, url, key, table_name):
        if not url or not key:
            raise ValueError("Supabase URL and Key must be provided.")

        # --- UPDATE: SPOOF USER AGENT ---
        # mimic a standard Chrome browser on Windows
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Connection": "keep-alive"
        }
        
        # Initialize client with custom headers
        self.client: Client = create_client(
            url, 
            key, 
            options=ClientOptions(headers=headers)
        )
        self.table_name = table_name

    def insert_batch_names(self, names_list):
        # ... (rest of the code remains the same)
        data = [{'name': name} for name in names_list]
        try:
            response = self.client.table(self.table_name).insert(data).execute()
            print(f"Batch inserted {len(names_list)} items into '{self.table_name}'.")
            return True
        except Exception as e:
            print(f"Error batch inserting data into '{self.table_name}': {e}")
            return False

    def get_table_count(self):
        # ... (rest of the code remains the same)
        try:
            response = self.client.table(self.table_name).select('*', count='exact', head=True).execute()
            if response.count is not None:
                return response.count
            else:
                print(f"Could not retrieve count from '{self.table_name}'.")
                return None
        except Exception as e:
            print(f"Error counting data in '{self.table_name}': {e}")
            return None

    def delete_batch_random_entries(self, limit=10):
        # ... (rest of the code remains the same)
        try:
            response = self.client.table(self.table_name).select('id').limit(1000).execute()
            if response.data:
                all_ids = [item['id'] for item in response.data]
                if not all_ids:
                    return True

                count_to_delete = min(len(all_ids), limit)
                ids_to_delete = random.sample(all_ids, count_to_delete)

                self.client.table(self.table_name).delete().in_('id', ids_to_delete).execute()
                print(f"Batch deleted {count_to_delete} entries from '{self.table_name}'.")
                return True
            else:
                return False
        except Exception as e:
            print(f"Error deleting data from '{self.table_name}': {e}")
            return False
