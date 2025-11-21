import os
import sys
import datetime


class OutputLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.log_file = None

        # Guardar las referencias originales
        self.stdout_original = sys.stdout if sys.stdout else sys.__stdout__
        self.stderr_original = sys.stderr if sys.stderr else sys.__stderr__

    def start(self):
        """Crea archivo de log y redirige stdout/stderr."""
        try:
            os.makedirs(self.log_dir, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"log_{timestamp}.txt"

            full_path = os.path.join(self.log_dir, filename)
            self.log_file = open(full_path, "w", encoding="utf-8")

            # Redirigir de forma segura
            sys.stdout = self
            sys.stderr = self

            self._write_direct(f"[INFO] Logging iniciado: {full_path}\n")

        except Exception as e:
            self._write_direct(f"[LOGGER ERROR] No se pudo iniciar logging: {e}\n")
            self.stop()

    def stop(self):
        """Detiene la redirección y devuelve stdout/stderr."""
        sys.stdout = self.stdout_original
        sys.stderr = self.stderr_original

        if self.log_file:
            try:
                self.log_file.close()
            except:
                pass

    # Redirección real
    def write(self, text):
        """Intercepta todos los prints y los envía al archivo."""
        try:
            if self.log_file:
                self.log_file.write(text)
                self.log_file.flush()
        except:
            pass  # Nunca crashear la app

    def flush(self):
        if self.log_file:
            try:
                self.log_file.flush()
            except:
                pass

    def _write_direct(self, text):
        """Escribe directamente al archivo evitando stdout."""
        try:
            if self.log_file:
                self.log_file.write(text)
                self.log_file.flush()
        except:
            pass
