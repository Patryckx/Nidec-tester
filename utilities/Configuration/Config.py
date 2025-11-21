import configparser
import os

from ui.Application import Ui_MainWindow as mainApplication
class Configuration():
    """ Configure functions """
    
    def __init__(self):       
        #connect signals
       pass

    def get_current_config(self):
        config = configparser.ConfigParser()

        try:
            config.read('settings/settings.ini')
            gateway_port = config.get('DAQ', 'address', fallback='None').replace('"', '')
            rs485_port = config.get('RS485', 'address', fallback='None').replace('"', '')
            rs232_port = config.get('RS232', 'address', fallback='None').replace('"', '')

            camera_address=config.get('Camera', 'address', fallback='None').replace('"', '')
            camera_port=config.get('Camera', 'port', fallback='None').replace('"', '')

            timer=config.get('Timer', 'cycle_time', fallback='None')

            led_program=config.get('Programs', 'led', fallback='None').replace('"', '')

            ocr_program=config.get('Programs', 'ocr', fallback='None').replace('"', '')
            return gateway_port,rs232_port, rs485_port,camera_address,camera_port,timer,led_program,ocr_program
        except Exception as e:
            print(f"Error reading settings.ini: {e}")
            return None,None,None,None,None,None

    def get_current_user(self):
        config = configparser.ConfigParser()
        session_path = 'settings/session.ini'

        # 1. Verificar que el archivo exista
        if not os.path.exists(session_path):
            print("session.ini not found.")
            return None, None

        try:
            config.read(session_path)

            # 2. Validar que exista la sección
            if 'Session' not in config:
                print("Missing 'Session' section in session.ini")
                return None, None

            # 3. Obtener valores de forma robusta
            user_id = config['Session'].get('ID_User', None)
            shop_order = config['Session'].get('Shop_order', None)

            # 4. Limpiar comillas solo si existen
            if user_id:
                user_id = user_id.strip().replace('"', '')
            if shop_order:
                shop_order = shop_order.strip().replace('"', '')

            return user_id, shop_order

        except Exception as e:
            print(f"Error reading session.ini: {e}")
            return None, None

    
    def save_new_configuration(self,gateway_port,rs232_port,rs485_port,camera_address,timer_value):
        try:
            
            # Crear un objeto ConfigParser
            config = configparser.ConfigParser()

            # Cargar el archivo .ini
            config.read('settings/settings.ini')

            # DAQ
            config.set('DAQ', 'address', gateway_port)
            # RS232
            config.set('RS232', 'address', rs232_port)
            # RS485
            config.set('RS485', 'address', rs485_port)
            # Camera
            config.set('Camera', 'address', camera_address)

            # Timer
            config.set('Timer', 'cycle_time', timer_value)

            # Guardar los cambios en el archivo .ini
            with open('settings/settings.ini', 'w') as configfile:
                config.write(configfile)
        except Exception as e:
            print("Error al guardar la configuracion",e)
    
    
    def save_new_user_and_shop_info(self, user_Id, Shop_order):
        try:
            session_path = 'settings/session.ini'

            # 1. Crear el directorio si no existe
            os.makedirs(os.path.dirname(session_path), exist_ok=True)

            config = configparser.ConfigParser()

            # 2. Cargar archivo existente si ya existe
            if os.path.exists(session_path):
                config.read(session_path)
            else:
                # 3. Crear archivo y sección nueva
                config['Session'] = {}

            # 4. Si la sección no existe, crearla
            if 'Session' not in config:
                config['Session'] = {}

            # 5. Validar valores de entrada
            user_Id = user_Id if user_Id not in (None, "") else "None"
            Shop_order = Shop_order if Shop_order not in (None, "") else "None"

            # 6. Guardar valores limpios
            config['Session']['ID_User'] = str(user_Id).strip()
            config['Session']['Shop_order'] = str(Shop_order).strip()

            # 7. Escribir archivo
            with open(session_path, 'w') as configfile:
                config.write(configfile)

        except Exception as e:
            print("Error al guardar la información del usuario y orden de compra:", e)

    def erase_user_and_shop_info(self):
        try:
            
            print("Erasing session info")
            # Crear un objeto ConfigParser
            config = configparser.ConfigParser()

            # Cargar el archivo .ini
            config.read('settings/session.ini')

            # DAQ
            config.set('Session', 'ID_User', "")
            # RS232
            config.set('Session', 'Shop_order', "")
            
            # Guardar los cambios en el archivo .ini
            with open('settings/session.ini', 'w') as configfile:
                config.write(configfile)
        except Exception as e:
            print("Error al borrar la informacion del usuario y orden de compra",e)


    ###################### POSTGRESS ###############################


    def get_sqlite_database_information(self):
        config = configparser.ConfigParser()

        try:
            config.read('settings/settings.ini')
           
            host=config.get('DATABASE', 'db_path', fallback='127.0.0.1').replace('"', '')

            table=config.get('DATABASE', 'table_name', fallback='"pentair-tester-registers"')



            return host,table
        except Exception as e:
            print(f"Error reading settings.ini: {e}")
            return None,None


