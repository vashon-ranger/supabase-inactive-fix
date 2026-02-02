# main.py

import json
import os
import logging
from helpers.utils import generate_secure_random_string
from services.supabase_service import SupabaseClient

# User-defined variables to toggle additional features
log_failed_databases = True 
detailed_status_report = True 

# Configure logging
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
        return
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing 'config.json': {e}")
        return

    all_successful = True
    failed_databases = [] if log_failed_databases else None
    status_report = [] if detailed_status_report else None

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
            if log_failed_databases:
                failed_databases.append(name)
            continue

        logging.info(f"Processing database: {name}")

        supabase_client = SupabaseClient(url, key, table_name)

        # --- BATCH INSERTION (10 Items) ---
        logging.info("Generating and inserting 10 random strings...")
        
        # Generate 10 random strings locally
        random_names_list = [generate_secure_random_string(10) for _ in range(10)]
        
        # Perform batch insert
        success_insert = supabase_client.insert_batch_names(random_names_list)
        
        if not success_insert:
            all_successful = False
            logging.error("Batch insertion failed.")
            if log_failed_databases:
                failed_databases.append(name)
            # Depending on logic, you might want to `continue` here. 
            # We proceed to check count/cleanup regardless.

        # --- CHECK COUNT ---
        count = supabase_client.get_table_count()
        if count is None:
            logging.error(f"Failed to get count for table '{table_name}'.")
            all_successful = False
            if log_failed_databases and name not in failed_databases:
                failed_databases.append(name)
            continue

        logging.info(f"Current entries in '{table_name}': {count}")

        # --- BATCH DELETION (Threshold > 100) ---
        success_delete = None
        if count > 100:
            logging.info(f"Count ({count}) > 100. Deleting 10 random entries...")
            success_delete = supabase_client.delete_batch_random_entries(limit=10)
            
            if not success_delete:
                all_successful = False
                logging.error("Batch deletion failed.")
                if log_failed_databases and name not in failed_databases:
                    failed_databases.append(name)
        else:
            logging.info(f"Count ({count}) is within limits. No deletion needed.")

        # --- STATUS REPORTING ---
        if detailed_status_report:
            status = {
                'name': name,
                'success_insert': success_insert,
                'success_delete': success_delete,
                'count': count
            }
            status_report.append(status)

    # --- FINAL LOGGING ---
    if all_successful:
        logging.info("All database actions were successful.")
    else:
        logging.warning("Some database actions failed.")
        if log_failed_databases and failed_databases:
            logging.warning("Failed databases:")
            for db_name in failed_databases:
                logging.warning(f"- {db_name}")

    if detailed_status_report and status_report:
        logging.info("\nDetailed Status Report:")
        for status in status_report:
            logging.info(f"Database: {status['name']}")
            logging.info(f"  Insert Batch (10): {status['success_insert']}")
            logging.info(f"  Total Count: {status['count']}")
            if status['success_delete'] is not None:
                logging.info(f"  Delete Batch (10): {status['success_delete']}")
            else:
                logging.info("  Delete Batch: N/A")

if __name__ == "__main__":
    main()
