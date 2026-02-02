# services/supabase_service.py

from supabase import create_client, Client
import random

class SupabaseClient:
    def __init__(self, url, key, table_name):
        if not url or not key:
            raise ValueError("Supabase URL and Key must be provided.")

        self.client: Client = create_client(url, key)
        self.table_name = table_name

    def insert_batch_names(self, names_list):
        """
        Inserts a list of names in a single API call.
        """
        # Prepare list of dictionaries
        data = [{'name': name} for name in names_list]
        try:
            response = self.client.table(self.table_name).insert(data).execute()
            print(f"Batch inserted {len(names_list)} items into '{self.table_name}'.")
            return True
        except Exception as e:
            print(f"Error batch inserting data into '{self.table_name}': {e}")
            return False

    def get_table_count(self):
        try:
            # count='exact' + head=True means we don't fetch the actual data rows, just the count
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
        """
        Deletes a specific number of random entries in a single API call.
        """
        try:
            # 1. Fetch IDs (limit the fetch to a reasonable number to pick from, e.g. 1000, or all)
            # We only need the 'id' column.
            response = self.client.table(self.table_name).select('id').limit(1000).execute()
            
            if response.data:
                all_ids = [item['id'] for item in response.data]
                
                if not all_ids:
                    print(f"No entries to delete in '{self.table_name}'.")
                    return True

                # 2. Randomly select up to 'limit' IDs
                # Use min() to handle cases where table has fewer rows than 'limit'
                count_to_delete = min(len(all_ids), limit)
                ids_to_delete = random.sample(all_ids, count_to_delete)

                # 3. Delete the selected IDs in one batch using the .in_() filter
                self.client.table(self.table_name).delete().in_('id', ids_to_delete).execute()
                
                print(f"Batch deleted {count_to_delete} entries from '{self.table_name}'.")
                return True
            else:
                print(f"No data retrieved from '{self.table_name}' for deletion.")
                return False
        except Exception as e:
            print(f"Error deleting data from '{self.table_name}': {e}")
            return False
