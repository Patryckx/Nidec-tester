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
            gateway_port = config.get('DAQ', 'address', fallback='None')
            rs485_port = config.get('RS485', 'address', fallback='None')
            rs232_port = config.get('RS232', 'address', fallback='None')

            camera_address=config.get('Camera', 'address', fallback='None')
            camera_port=config.get('Camera', 'port', fallback='None')

            timer=config.get('Timer', 'cycle_time', fallback='None')
            return gateway_port, rs485_port, rs485_port, rs232_port,camera_address,camera_port,timer
        except Exception as e:
            print(f"Error reading settings.ini: {e}")
            return None,None,None,None,None,None


    def show_current_configuration(self, event):

        current_config=self.get_current_config()

        gateway_port=current_config[0]
        RS232_port=current_config[1]
        RS485_port=current_config[2]
        camera_address=current_config[3]
        camera_port=current_config[4]
        timer=current_config[5]
        
       


        #Show first screen of stacked widget
        self.ui.stackedWidget.setCurrentIndex(0)

        

    def show_set_configuration(self,event):

        #Put information in Configuration GUI

    
        #DAQ
        if self.daq_stat.lower()=="true":
            self.ui.daqcombobox.setCurrentText("Habilitado")
        elif self.daq_stat.lower()=="false":
            self.ui.daqcombobox.setCurrentText("Deshabilitado")
        #self.configuration_app.ui.txtdaqenabled.setText(str(self.daq_stat))
        
        #Display information in Gui

        self.ui.txtdaqport.setText(str(self.daq_port))

        self.ui.txtEthernet_address.setText(str(self.ethernet_address))
        self.ui.txtEthernetPort.setText(str(self.ethernet_port))

    
    
    def save_new_configuration(self, event):
        self.ui.lbltxtfilltexfields.setText("")

        if self.ui.txtdaqport.text() and self.ui.txtEthernetPort.text() and self.ui.txtEthernet_address :
            # Get parameters from textfields

            # DAQ
            # Status
            self.daq_new_status = self.ui.daqcombobox.currentText()

            if self.daq_new_status == "Habilitado":
                self.daq_enabled = '"true"'
            elif self.daq_new_status == "Deshabilitado":
                self.daq_enabled = '"false"'
            else:
                print("Opción no reconocida")          

            # Port
            self.new_daqport = self.ui.txtdaqport.text()

           # Search for digits in new_daqport
            search_result = re.search(r'\d+', self.new_daqport)

            # Fallback to prevent empty COM port input in config
            if search_result is None:
                self.daqport_new_number = int(1)  # Default value
            else:
                self.daqport_new_number = search_result.group()
            

            self.daqport_new_port_string = f'"COM{str(self.daqport_new_number)}"'

            #Ethernet

            self.new_ethernet_address=self.ui.txtEthernet_address.text()

            self.new_ethernet_port=self.ui.txtEthernetPort.text()

            # Modify variables to save in configuration

            # Overwrite configuration

            # Crear un objeto ConfigParser
            config = configparser.ConfigParser()

            # Cargar el archivo .ini
            config.read('settings/settings.ini')

           

            # DAQ
            config.set('DAQ', 'address', self.daqport_new_port_string)
            config.set('DAQ', 'enabled', self.daq_enabled)

            # Ethernet
            config.set('Ethernet', 'address', self.new_ethernet_address)
            config.set('Ethernet', 'port', self.new_ethernet_port)

            # Guardar los cambios en el archivo .ini
            with open('settings/settings.ini', 'w') as configfile:
                config.write(configfile)

            # Close screen once we save the configurations successfully
            self.close_configuration_screen()

        else:
            self.ui.lbltxtfilltexfields.setText("Por favor rellena todos los campos")
            print("Por favor, completa todos los campos antes de guardar la configuración.")


    def daq_information(self):
        # Read model configurations
        config = configparser.ConfigParser()
        #config.read('engine/settings/instrument_settings.ini')
        config.read('settings/settings.ini')
        
        daq_status = str(config['DAQ']['enabled'].replace('"', ''))
        daq_port = str(config['DAQ']['address'].replace('"', ''))

        return daq_status, daq_port
    
    def ethernet_information(self):
        # Read model configurations
        config = configparser.ConfigParser()
        #config.read('engine/settings/instrument_settings.ini')
        config.read('settings/settings.ini')
        
        ethernet_address = str(config['Ethernet']['address'].replace('"', ''))
        ethernet_port = str(config['Ethernet']['port'].replace('"', ''))

        return ethernet_address, ethernet_port
    
    
    def back_showconfiguration(self,event):
        self.ui.stackedWidget.setCurrentIndex(0) 

    
    def close_configuration_screen(self):
        self.hide()
