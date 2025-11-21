# logger_redirect.py

import os
import sys
import datetime

class OutputLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.log_file = None

        # Mantener referencia a stdout/stderr originales
        self.stdout_original = sys.stdout
        self.stderr_original = sys.stderr

    def start(self):
        """Crea archivo de log y redirige stdout/stderr."""
        try:
            # Crear carpeta incluso si es ruta absoluta
            os.makedirs(self.log_dir, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"log_{timestamp}.txt"
            full_path = os.path.join(self.log_dir, filename)

            # Abrir archivo de log
            self.log_file = open(full_path, "w", encoding="utf-8")

            # Crear redireccion que escribe en consola Y archivo
            class Redirector:
                def __init__(self, stream_console, stream_file):
                    self.console = stream_console
                    self.file = stream_file

                def write(self, message):
                    if message.strip() != "":
                        self.console.write(message)
                    self.file.write(message)

                def flush(self):
                    self.console.flush()
                    self.file.flush()

            sys.stdout = Redirector(self.stdout_original, self.log_file)
            sys.stderr = Redirector(self.stderr_original, self.log_file)

            print(f"[LOG INIT] Logging iniciado en: {full_path}")

        except Exception as e:
            print("ERROR al iniciar logging:", e)
            self.stop()

    def stop(self):
        """Restaura stdout/stderr originales."""
        sys.stdout = self.stdout_original
        sys.stderr = self.stderr_original

        if self.log_file:
            self.log_file.close()
            self.log_file = None
