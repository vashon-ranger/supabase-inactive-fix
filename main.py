# main.py

import json
import os
import logging
import sys
import random  # <--- NEW IMPORT
from helpers.utils import generate_secure_random_string
from services.supabase_service import SupabaseClient

# --- CONFIGURATION ---
MIN_BATCH_SIZE = 10      # Minimum items to insert/delete
MAX_BATCH_SIZE = 30      # Maximum items to insert/delete
MAX_ROW_COUNT = 100      # Max rows allowed before deletion triggers
LOG_FAILED_DBS = True    
DETAILED_REPORT = True   
# ---------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    try:
        with open('config.json', 'r') as config_file:
            configs = json.load(config_file)
    except FileNotFoundError:
        logging.error("Configuration file 'config.json' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing 'config.json': {e}")
        sys.exit(1)

    all_successful = True
    failed_databases = [] if LOG_FAILED_DBS else None
    status_report = [] if DETAILED_REPORT else None

    for config in configs:
        name = config.get('name', 'Unnamed Database')
        url = config.get('supabase_url')
        key = config.get('supabase_key')
        table_name = config.get('table_name', 'KeepAlive')

        key_env_var = config.get('supabase_key_env')
        if key_env_var:
            key = os.getenv(key_env_var)

        if not url or not key:
            logging.error(f"Supabase URL or Key missing for '{name}'. Skipping.")
            all_successful = False
            if LOG_FAILED_DBS:
                failed_databases.append(name)
            continue

        logging.info(f"Processing database: {name}")

        try:
            supabase_client = SupabaseClient(url, key, table_name)

            # --- 1. READ ACTIVITY (Force a "Wake Up") ---
            # Instead of just counting, we fetch a few rows to force a READ event
            supabase_client.client.table(table_name).select("name").limit(5).execute()

            # --- 2. WRITE ACTIVITY (Random Batch Insert) ---
            # Calculate a unique random batch size for THIS specific run/table
            current_insert_size = random.randint(MIN_BATCH_SIZE, MAX_BATCH_SIZE)
            
            logging.info(f"Generating and inserting {current_insert_size} random strings...")
            random_names_list = [generate_secure_random_string(10) for _ in range(current_insert_size)]
            
            success_insert = supabase_client.insert_batch_names(random_names_list)
            
            if not success_insert:
                all_successful = False
                if LOG_FAILED_DBS:
                    failed_databases.append(name)

            # --- 3. COUNT CHECK ---
            count = supabase_client.get_table_count()
            if count is None:
                all_successful = False
                continue

            logging.info(f"Current entries in '{table_name}': {count}")

            # --- 4. DELETE ACTIVITY (Smart Random Delete) ---
            success_delete = None
            
            if count > MAX_ROW_COUNT:
                # Calculate how many we MUST delete to get back to the limit
                excess = count - MAX_ROW_COUNT
                
                # Generate a random delete amount for variety
                random_delete_target = random.randint(MIN_BATCH_SIZE, MAX_BATCH_SIZE)
                
                # Logic: Delete the GREATER of:
                # A) The excess amount + 1 (to ensure we definitely go BELOW the limit)
                # B) The random amount (to ensure we delete a decent chunk if excess is small)
                rows_to_delete = max(excess + 1, random_delete_target)
                
                logging.info(f"Count > {MAX_ROW_COUNT}. Excess is {excess}. Deleting {rows_to_delete} entries...")
                
                success_delete = supabase_client.delete_batch_random_entries(limit=rows_to_delete)
                if not success_delete:
                    all_successful = False
            else:
                 logging.info(f"Count ({count}) is within limit ({MAX_ROW_COUNT}). No deletion needed.")
            
            # Reporting
            if DETAILED_REPORT:
                status_report.append({
                    'name': name,
                    'success_insert': success_insert,
                    'success_delete': success_delete,
                    'count': count,
                    'inserted_amount': current_insert_size 
                })

        except Exception as e:
            logging.error(f"Critical error processing '{name}': {e}")
            all_successful = False
            if LOG_FAILED_DBS:
                failed_databases.append(name)

    # --- FINAL REPORT ---
    if DETAILED_REPORT and status_report:
        logging.info("\nDetailed Status Report:")
        for status in status_report:
            # Safely handle 'inserted_amount' key for display
            ins_amt = status.get('inserted_amount', 'N/A')
            logging.info(f"Database: {status['name']} | Count: {status['count']} | Inserted: {ins_amt} | Success: {status['success_insert']}")

    if not all_successful:
        logging.error("Exiting with failure code.")
        sys.exit(1)

if __name__ == "__main__":
    main()
