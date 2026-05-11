import configparser
import os


class Configuration:
    """ Configure functions """

    SETTINGS_FILE = 'settings/settings.ini'
    SESSION_FILE = 'settings/session.ini'

    def __init__(self):
        pass

    # =========================================================
    # INTERNAL METHODS
    # =========================================================

    def load_config(self, file_path):
        config = configparser.ConfigParser()

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                config.read_file(f)

            return config

        except FileNotFoundError:
            print(f"Configuration file not found: {file_path}")
            return None

        except Exception as e:
            print(f"Error reading config file {file_path}: {e}")
            return None

    def save_config(self, config, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)

            return True

        except Exception as e:
            print(f"Error saving config file {file_path}: {e}")
            return False

    def ensure_section(self, config, section):
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

            gateway_port = config.get('DAQ', 'address', fallback='None').strip()

            rs485_port = config.get('RS485', 'address', fallback='None').strip()

            rs232_port = config.get('RS232', 'address', fallback='None').strip()

            camera_address = config.get('Camera', 'address', fallback='None').strip()

            camera_port = config.get('Camera', 'port', fallback='None').strip()

            timer = config.get('Timer', 'cycle_time', fallback='None').strip()

            led_program = config.get('Programs', 'led', fallback='None').strip()

            ocr_program = config.get('Programs', 'ocr', fallback='None').strip()

            return (
                gateway_port,
                rs232_port,
                rs485_port,
                camera_address,
                camera_port,
                timer,
                led_program,
                ocr_program
            )

        except Exception as e:
            print(f"Error reading settings values: {e}")
            return (None,) * 8

    # =========================================================
    # SESSION
    # =========================================================

    def get_current_user(self):

        config = self.load_config(self.SESSION_FILE)

        if config is None:
            return None, None

        try:

            if not config.has_section('Session'):
                raise ValueError("Section [Session] does not exist")

            user_id = config.get(
                'Session',
                'id_user',
                fallback=''
            ).strip()

            shop_order = config.get(
                'Session',
                'shop_order',
                fallback=''
            ).strip()

            return user_id, shop_order

        except Exception as e:
            print(f"Error reading session data: {e}")
            return None, None

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

            sections = [
                'DAQ',
                'RS232',
                'RS485',
                'Camera',
                'Timer'
            ]

            for section in sections:
                self.ensure_section(config, section)

            config.set('DAQ', 'address', str(gateway_port))

            config.set('RS232', 'address', str(rs232_port))

            config.set('RS485', 'address', str(rs485_port))

            config.set('Camera', 'address', str(camera_address))

            config.set('Timer', 'cycle_time', str(timer_value))

            self.save_config(config, self.SETTINGS_FILE)

        except Exception as e:
            print(f"Error saving configuration: {e}")

    # =========================================================
    # SAVE SESSION
    # =========================================================

    def save_new_user_and_shop_info(self, user_id, shop_order):

        config = self.load_config(self.SESSION_FILE)

        if config is None:
            config = configparser.ConfigParser()

        try:

            self.ensure_section(config, 'Session')

            config.set('Session', 'id_user', str(user_id))

            config.set('Session', 'shop_order', str(shop_order))

            self.save_config(config, self.SESSION_FILE)

        except Exception as e:
            print(f"Error saving user/shop info: {e}")

    def erase_user_and_shop_info(self):

        config = self.load_config(self.SESSION_FILE)

        if config is None:
            config = configparser.ConfigParser()

        try:

            self.ensure_section(config, 'Session')

            config.set('Session', 'id_user', '')

            config.set('Session', 'shop_order', '')

            self.save_config(config, self.SESSION_FILE)

            print("Session info erased")

        except Exception as e:
            print(f"Error erasing session info: {e}")

    # =========================================================
    # SQLITE
    # =========================================================

    def get_sqlite_database_information(self):

        config = self.load_config(self.SETTINGS_FILE)

        if config is None:
            return None, None

        try:

            host = config.get(
                'DATABASE',
                'db_path',
                fallback='127.0.0.1'
            ).strip()

            table = config.get(
                'DATABASE',
                'table_name',
                fallback='pentair-tester-registers'
            ).strip()

            return host, table

        except Exception as e:
            print(f"Error reading database information: {e}")
            return None, None