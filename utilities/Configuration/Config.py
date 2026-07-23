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

    @staticmethod
    def _clean(value: str) -> str:
        """
        Elimina espacios y comillas dobles/simples de un valor leído del .ini.
        Uso: self._clean(config.get(...))
        """
        return value.strip().strip('"').strip("'")

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
            print(f"[Config] Error checking file integrity {file_path}: {e}")
            return True                             # ante la duda, tratar como corrupto

    def _backup_and_recreate(self, file_path: str):
        """
        Hace una copia del archivo corrupto con timestamp
        y lo elimina para que sea recreado limpio.
        """
        try:
            timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.corrupt_{timestamp}.bak"
            shutil.copy2(file_path, backup_path)
            os.remove(file_path)
            print(f"[Config] Archivo corrupto respaldado en: {backup_path}")
        except Exception as e:
            print(f"[Config] Error al respaldar archivo corrupto {file_path}: {e}")

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
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(tmp_path, 'w', encoding='utf-8') as f:
                config.write(f)
                f.flush()
                os.fsync(f.fileno())               # forzar escritura a disco

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
            gateway_port   = self._clean(config.get('DAQ',      'address',    fallback='None'))
            rs485_port     = self._clean(config.get('RS485',    'address',    fallback='None'))
            rs232_port     = self._clean(config.get('RS232',    'address',    fallback='None'))
            camera_address = self._clean(config.get('Camera',   'address',    fallback='None'))
            camera_port    = self._clean(config.get('Camera',   'port',       fallback='None'))
            timer          = self._clean(config.get('Timer',    'cycle_time', fallback='None'))
            led_program    = self._clean(config.get('Programs', 'led',        fallback='None'))
            ocr_program    = self._clean(config.get('Programs', 'ocr',        fallback='None'))

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
            return '', ''

        try:
            if not config.has_section('Session'):
                return '', ''

            user_id    = self._clean(config.get('Session', 'id_user',    fallback=''))
            shop_order = self._clean(config.get('Session', 'shop_order', fallback=''))

            return user_id, shop_order

        except Exception as e:
            print(f"[Config] Error leyendo sesión: {e}")
            return '', ''

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
            host  = self._clean(config.get('DATABASE', 'db_path',    fallback=''))
            table = self._clean(config.get('DATABASE', 'table_name', fallback='pentair-tester-registers'))

            return host, table

        except Exception as e:
            print(f"[Config] Error leyendo información de base de datos: {e}")
            return '', ''
    # =========================================================
    # LCD_SHORT_CIRCUIT_TEST_CONFIG
    # =========================================================
    def get_lcd_short_circuit_config(self):

        config = self.load_config(self.SETTINGS_FILE)

        if config is None:
            return {}

        return {

            "3": {
                "program": self._clean(
                    config.get("LCD_short_circuit_test", "program_3")
                ),
                "command": "FF00FFA50060100D07D05D04333333330326"
            },

            "H": {
                "program": self._clean(
                    config.get("LCD_short_circuit_test", "program_H")
                ),
                "command": "FF00FFA50060100D07D05D0448484848037A"
            },

            "O": {
                "program": self._clean(
                    config.get("LCD_short_circuit_test", "program_O")
                ),
                "command": "FF00FFA50060100D07D05D044F4F4F4F0396"
            },

            "C": {
                "program": self._clean(
                    config.get("LCD_short_circuit_test", "program_C")
                ),
                "command": "FF00FFA50060100D07D05D04434343430366"
            }

        }