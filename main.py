import json
import os
import logging
import sys  # <--- IMPORT SYS MODULE
from helpers.utils import generate_secure_random_string
from services.supabase_service import SupabaseClient

# --- CONFIGURATION ---
BATCH_SIZE = 20          # Number of rows to insert (and delete) per run
MAX_ROW_COUNT = 100      # Max rows allowed before deletion triggers
LOG_FAILED_DBS = True    # Log failed databases
DETAILED_REPORT = True   # Generate detailed status report
# ---------------------

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
        sys.exit(1) # <--- EXIT WITH FAILURE
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing 'config.json': {e}")
        sys.exit(1) # <--- EXIT WITH FAILURE

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

        supabase_client = SupabaseClient(url, key, table_name)

        # --- BATCH INSERTION ---
        logging.info(f"Generating and inserting {BATCH_SIZE} random strings...")
        
        # Generate random strings locally using the global BATCH_SIZE
        random_names_list = [generate_secure_random_string(10) for _ in range(BATCH_SIZE)]
        
        # Perform batch insert
        success_insert = supabase_client.insert_batch_names(random_names_list)
        
        if not success_insert:
            all_successful = False
            logging.error("Batch insertion failed.")
            if LOG_FAILED_DBS:
                failed_databases.append(name)

        # --- CHECK COUNT ---
        count = supabase_client.get_table_count()
        if count is None:
            logging.error(f"Failed to get count for table '{table_name}'.")
            all_successful = False
            if LOG_FAILED_DBS and name not in failed_databases:
                failed_databases.append(name)
            continue

        logging.info(f"Current entries in '{table_name}': {count}")

        # --- BATCH DELETION ---
        success_delete = None
        if count > MAX_ROW_COUNT:
            logging.info(f"Count ({count}) > {MAX_ROW_COUNT}. Deleting {BATCH_SIZE} random entries...")
            success_delete = supabase_client.delete_batch_random_entries(limit=BATCH_SIZE)
            
            if not success_delete:
                all_successful = False
                logging.error("Batch deletion failed.")
                if LOG_FAILED_DBS and name not in failed_databases:
                    failed_databases.append(name)
        else:
            logging.info(f"Count ({count}) is within limit ({MAX_ROW_COUNT}). No deletion needed.")

        # --- STATUS REPORTING ---
        if DETAILED_REPORT:
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
        if LOG_FAILED_DBS and failed_databases:
            logging.warning("Failed databases:")
            for db_name in failed_databases:
                logging.warning(f"- {db_name}")

    if DETAILED_REPORT and status_report:
        logging.info("\nDetailed Status Report:")
        for status in status_report:
            logging.info(f"Database: {status['name']}")
            logging.info(f"  Insert Batch ({BATCH_SIZE}): {status['success_insert']}")
            logging.info(f"  Total Count: {status['count']}")
            if status['success_delete'] is not None:
                logging.info(f"  Delete Batch ({BATCH_SIZE}): {status['success_delete']}")
            else:
                logging.info("  Delete Batch: N/A")

    # --- EXIT WITH ERROR CODE IF ANY FAILURES OCCURRED ---
    if not all_successful:
        logging.error("Exiting with failure code because one or more databases failed.")
        sys.exit(1)  # <--- THIS TELLS GITHUB ACTIONS TO FAIL THE WORKFLOW

if __name__ == "__main__":
    main()
