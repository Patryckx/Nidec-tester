# logger_config.py
import logging
import os
import configparser
from datetime import datetime

def setup_logger():

    config = configparser.ConfigParser()
    config.read("config.ini", encoding="utf-8")

    enable_logs = config.getboolean("LOGGING", "enable_logs", fallback=True)

    if not enable_logs:
        # Si está desactivado, no configurar logging
        print("Sistema de logs desactivado por configuración.")
        return None

    logs_dir = r"C:/Nidec Pentair Tester error logs"
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
    log_path = os.path.join(logs_dir, log_filename)

    logging.basicConfig(
        level=logging.ERROR,  # Puedes usar INFO, WARNING, DEBUG según necesites
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()  # Muestra también en consola
        ]
    )
