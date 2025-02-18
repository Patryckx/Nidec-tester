import configparser

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

            led_program=config.get('Programs', 'led', fallback='None')

            ocr_program=config.get('Programs', 'ocr', fallback='None')
            return gateway_port,rs232_port, rs485_port,camera_address,camera_port,timer,led_program,ocr_program
        except Exception as e:
            print(f"Error reading settings.ini: {e}")
            return None,None,None,None,None,None

    def get_current_user(self):
        config = configparser.ConfigParser()
        try:
            config.read('settings/session.ini')
            user_Id = config.get('Session', 'ID_User', fallback='None').replace('"', '')
            shop_Order = config.get('Session', 'Shop_order', fallback='None').replace('"', '')
           
            return user_Id,shop_Order
        except Exception as e:
            print(f"Error reading session.ini: {e}")
            return None,None

    
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
    
    
    def save_new_user_and_shop_info(self,user_Id,Shop_order):
        try:
            
            # Crear un objeto ConfigParser
            config = configparser.ConfigParser()

            # Cargar el archivo .ini
            config.read('settings/session.ini')

            # DAQ
            config.set('Session', 'ID_User', user_Id)
            # RS232
            config.set('Session', 'Shop_order', Shop_order)
            
            # Guardar los cambios en el archivo .ini
            with open('settings/session.ini', 'w') as configfile:
                config.write(configfile)
        except Exception as e:
            print("Error al guardar la informacion del usuario y orden de compra",e)

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

