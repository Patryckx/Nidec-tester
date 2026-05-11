import configparser
import os
import shutil
from datetime import datetime


class Configuration:
    """ Configure functions """

    SETTINGS_FILE = 'settings/settings.ini'
    SESSION_FILE  = 'settings/session.ini'

    def __init__(self):
        pass

    # =========================================================
    # INTERNAL METHODS
    # =========================================================

    def _is_file_corrupt(self, file_path: str) -> bool:
        """
        Detecta si un archivo .ini está corrupto (vacío, solo nulos,
        o sin encabezados de sección válidos).
        """
        try:
            if not os.path.exists(file_path):
                return False                        # no existe aún — no es corrupción

            size = os.path.getsize(file_path)
            if size == 0:
                return True                         # archivo vacío

            with open(file_path, 'rb') as f:
                raw = f.read(512)                   # leer solo los primeros 512 bytes

            # Si más del 30 % son bytes nulos → corrupto
            null_ratio = raw.count(b'\x00') / len(raw)
            if null_ratio > 0.30:
                return True

            return False

        except Exception as e:
            print(f"Error checking file integrity {file_path}: {e}")
            return True                             # ante la duda, tratar como corrupto

    def _backup_and_recreate(self, file_path: str):
        """
        Hace una copia del archivo corrupto con timestamp
        y lo elimina para que sea recreado limpio.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.corrupt_{timestamp}.bak"
            shutil.copy2(file_path, backup_path)
            os.remove(file_path)
            print(f"Archivo corrupto respaldado en: {backup_path}")
        except Exception as e:
            print(f"Error al respaldar archivo corrupto {file_path}: {e}")

    def load_config(self, file_path: str) -> configparser.ConfigParser | None:
        """
        Carga un archivo .ini con detección de corrupción y recuperación automática.
        """
        # ── 1. Detectar corrupción antes de intentar leer ──────────────
        if self._is_file_corrupt(file_path):
            print(f"[Config] Archivo corrupto detectado: {file_path}. Recreando...")
            self._backup_and_recreate(file_path)
            return None                             # el llamador usará valores fallback

        # ── 2. Lectura normal ──────────────────────────────────────────
        config = configparser.ConfigParser()
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                config.read_file(f)
            return config

        except configparser.MissingSectionHeaderError:
            # El archivo existe pero no tiene secciones válidas
            print(f"[Config] Sin encabezados de sección en: {file_path}. Recreando...")
            self._backup_and_recreate(file_path)
            return None

        except FileNotFoundError:
            print(f"[Config] Archivo no encontrado: {file_path}")
            return None

        except Exception as e:
            print(f"[Config] Error leyendo {file_path}: {e}")
            return None

    def save_config(self, config: configparser.ConfigParser, file_path: str) -> bool:
        """
        Escritura atómica: escribe en un archivo temporal y solo
        reemplaza el original si la escritura fue exitosa.
        Evita dejar el .ini corrupto si la app se cierra a mitad de escritura.
        """
        tmp_path = file_path + ".tmp"
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Escribir en temporal primero
            with open(tmp_path, 'w', encoding='utf-8') as f:
                config.write(f)
                f.flush()
                os.fsync(f.fileno())               # forzar escritura a disco

            # Reemplazar el original solo si el temporal es válido
            if os.path.getsize(tmp_path) > 0:
                shutil.move(tmp_path, file_path)
                return True
            else:
                print(f"[Config] Archivo temporal vacío, no se reemplazó {file_path}")
                return False

        except Exception as e:
            print(f"[Config] Error guardando {file_path}: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False

    def ensure_section(self, config: configparser.ConfigParser, section: str):
        if not config.has_section(section):
            config.add_section(section)

    # =========================================================
    # SETTINGS
    # =========================================================

    def get_current_config(self):

        config = self.load_config(self.SETTINGS_FILE)

        if config is None:
            return (None,) * 8

        try:
            gateway_port  = config.get('DAQ',      'address',    fallback='None').strip()
            rs485_port    = config.get('RS485',     'address',    fallback='None').strip()
            rs232_port    = config.get('RS232',     'address',    fallback='None').strip()
            camera_address= config.get('Camera',    'address',    fallback='None').strip()
            camera_port   = config.get('Camera',    'port',       fallback='None').strip()
            timer         = config.get('Timer',     'cycle_time', fallback='None').strip()
            led_program   = config.get('Programs',  'led',        fallback='None').strip()
            ocr_program   = config.get('Programs',  'ocr',        fallback='None').strip()

            return (
                gateway_port, rs232_port, rs485_port,
                camera_address, camera_port, timer,
                led_program, ocr_program
            )

        except Exception as e:
            print(f"[Config] Error leyendo settings: {e}")
            return (None,) * 8

    # =========================================================
    # SESSION
    # =========================================================

    def get_current_user(self) -> tuple[str, str]:
        """
        Retorna (user_id, shop_order).
        Garantiza strings vacíos en lugar de None cuando no hay sesión.
        """
        config = self.load_config(self.SESSION_FILE)

        if config is None:
            return '', ''                           # ← nunca retorna None

        try:
            if not config.has_section('Session'):
                return '', ''

            user_id    = config.get('Session', 'id_user',    fallback='').strip()
            shop_order = config.get('Session', 'shop_order', fallback='').strip()

            return user_id, shop_order

        except Exception as e:
            print(f"[Config] Error leyendo sesión: {e}")
            return '', ''                           # ← nunca retorna None

    # =========================================================
    # SAVE SETTINGS
    # =========================================================

    def save_new_configuration(
        self,
        gateway_port,
        rs232_port,
        rs485_port,
        camera_address,
        timer_value
    ):
        config = self.load_config(self.SETTINGS_FILE)
        if config is None:
            config = configparser.ConfigParser()

        try:
            for section in ['DAQ', 'RS232', 'RS485', 'Camera', 'Timer']:
                self.ensure_section(config, section)

            config.set('DAQ',    'address',    str(gateway_port))
            config.set('RS232',  'address',    str(rs232_port))
            config.set('RS485',  'address',    str(rs485_port))
            config.set('Camera', 'address',    str(camera_address))
            config.set('Timer',  'cycle_time', str(timer_value))

            self.save_config(config, self.SETTINGS_FILE)

        except Exception as e:
            print(f"[Config] Error guardando configuración: {e}")

    # =========================================================
    # SAVE SESSION
    # =========================================================

    def save_new_user_and_shop_info(self, user_id: str, shop_order: str):

        config = self.load_config(self.SESSION_FILE)
        if config is None:
            config = configparser.ConfigParser()

        try:
            self.ensure_section(config, 'Session')
            config.set('Session', 'id_user',    str(user_id))
            config.set('Session', 'shop_order', str(shop_order))
            self.save_config(config, self.SESSION_FILE)

        except Exception as e:
            print(f"[Config] Error guardando sesión: {e}")

    def erase_user_and_shop_info(self):

        config = self.load_config(self.SESSION_FILE)
        if config is None:
            config = configparser.ConfigParser()

        try:
            self.ensure_section(config, 'Session')
            config.set('Session', 'id_user',    '')
            config.set('Session', 'shop_order', '')
            self.save_config(config, self.SESSION_FILE)
            print("[Config] Sesión borrada.")

        except Exception as e:
            print(f"[Config] Error borrando sesión: {e}")

    # =========================================================
    # SQLITE
    # =========================================================

    def get_sqlite_database_information(self) -> tuple[str, str]:

        config = self.load_config(self.SETTINGS_FILE)
        if config is None:
            return '', ''

        try:
            host = config.get(
                'DATABASE', 'db_path',
                fallback='127.0.0.1'
            ).strip()

            table = config.get(
                'DATABASE', 'table_name',
                fallback='pentair-tester-registers'
            ).strip()

            return host, table

        except Exception as e:
            print(f"[Config] Error leyendo información de base de datos: {e}")
            return '', ''