import logging
import os

def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(f"{log_dir}/bot.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
