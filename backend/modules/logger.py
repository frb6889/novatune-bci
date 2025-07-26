# logger.py
import csv, os
from datetime import datetime

def save_midi_log(records, log_dir="./log"):
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"midi_key_log_{timestamp}.csv"
    output_file = os.path.join(log_dir, log_filename)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['note', 'start_time', 'end_time', 'duration', 'velocity'])
        writer.writeheader()
        writer.writerows(records)
    return output_file
