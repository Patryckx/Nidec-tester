from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton

from ui.Application import Ui_MainWindow as mainApplication

#Instruments
from utilities.DAQ.DAQ import FX3U
from utilities.Telnet_lib.telnet import TelnetClient
from utilities.PySerial.PySerial_lib import SerialDevice
from utilities.Configuration.Config import Configuration
from utilities.Tests.Tests import Manage_tests


#from utilities.Config.Configuration import Config_Screen

# Custom imports
#import qdarktheme
from datetime import datetime

from datetime import datetime, timedelta
import configparser
import time
import os
import csv
import threading
import json 

import subprocess
import re

import socket
import telnetlib



class MainWindow(QMainWindow, mainApplication):

#Signals 

    Test_2_signal = pyqtSignal()

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        



        self.connect_signals()

        # Eliminar la barra de título y los botones de control
        self.setWindowFlags(Qt.FramelessWindowHint)
        #self.setWindowState(Qt.WindowFullScreen)  # Pantalla completa

        self.setMouseTracking(True)  # Seguimiento del mouse
        self._startPos = None  # Para guardar la posición inicial del mouse

        '''# Formato a tabla
        headers = ['ID','Codigo','Resultado', 'Programa','Hora' ]
        # Ajustar el ancho de una columna específica (por ejemplo, la columna "Resultado")
        id_column_index = headers.index('ID')
        self.ResultsTable.setColumnWidth(id_column_index, 60)  # Ajusta el ancho según sea necesario

        code_column_index = headers.index('Codigo')
        self.ResultsTable.setColumnWidth(code_column_index, 160)  # Ajusta el ancho según sea necesario

        program_column_index = headers.index('Programa')
        self.ResultsTable.setColumnWidth(program_column_index, 140)  # Ajusta el ancho según sea necesario

        result_column_index = headers.index('Resultado')
        self.ResultsTable.setColumnWidth(result_column_index, 140)  # Ajusta el ancho según sea necesario

        hora_column_index = headers.index('Hora')
        self.ResultsTable.setColumnWidth(hora_column_index, 190)  # Ajusta el ancho según sea necesario

        # Show first message stacked widget in GUI 
        self.stackedWidget_messages.setCurrentIndex(0)

        # Instance to configuration screen
        ########## Configuration ##########
        self.configuration_app = Config_Screen()

        self.session_app=Session()'''

        #Instance config class
        self.config=Configuration()

        self.gateway=FX3U()

        self.test=Manage_tests()

        

        # Space bar function initialized flag 
        self.initialized_flag = None

        # Ethernet connection instance
        self.controller = None

        self.tn=None

        self.plc=None

        #Threading event scan 
        self.keep_scanning = threading.Event()
        
        '''#Disable stop button 
        self.lblstop.setEnabled(False)
        #Disable stop button 
        self.lblEnter.setEnabled(False)

        #Disable txt field
        self.txtCode.setEnabled(False)'''

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._startPos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._startPos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._startPos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._startPos = None
            event.accept()

    def keyPressEvent(self, event):
        
        if event.key() == Qt.Key_Space and self.initialized_flag is None:
            # Initialize application pressing Space Bar
            print("space bar pressed")
            self.inicialize(event)

        if event.key() == Qt.Key_Return and self.initialized_flag ==True :  
            # Aquí se ejecuta la acción al presionar Enter
            print("Se presionó Enter")
            #self.get_validate_Mspec()
            self.Validate_Barcode_and_response(event)
  

    def connect_signals(self):
        self.lblinicialize.mousePressEvent = self.inicialize

        #Config button
        self.btnConfiguracion.clicked.connect(self.show_configuration)
        self.lblEditar.mousePressEvent = self.show_edit_screen_configuration
        self.lblGuardar.mousePressEvent = self.save_configuration
        self.lblCancelar.mousePressEvent = self.show_configuration

        #User ID and Shop order 
        self.lblConfirmUserInfo.mousePressEvent = self.confirm_and_save_userId_and_ShopOrder
        self.lblDenyUserInfo.mousePressEvent = self.deny_userId_and_ShopOrder

        self.btnVerificarDatos.clicked.connect(self.verify_user_and_ShopOrder)


        #Home Button
        self.btnInicializar.clicked.connect(self.back_to_inicialize_app)


        #Error buttons
        self.btnCameraErrorOK.clicked.connect(self.back_to_inicialize_app)
        self.btnGatewayErrorOK.clicked.connect(self.back_to_inicialize_app)
        self.btnSerialErrorOK.clicked.connect(self.back_to_inicialize_app)

        #Placeholder text with style configuration screeen

        # Connect focus event to clear the placeholder text and reset style
        self.txtGatewayPort.focusInEvent = lambda event: self.clear_placeholder_and_reset_style(self.txtGatewayPort, event)
        self.txt232Port.focusInEvent = lambda event: self.clear_placeholder_and_reset_style(self.txt232Port, event)
        self.txt485Port.focusInEvent = lambda event: self.clear_placeholder_and_reset_style(self.txt485Port, event)
        self.txtCameraAddress.focusInEvent = lambda event: self.clear_placeholder_and_reset_style(self.txtCameraAddress, event)

        #User ID and Shop order textboxes
        self.txtNumeroEmpleado.focusInEvent = lambda event: self.clear_placeholder_and_reset_style(self.txtNumeroEmpleado, event)
        self.txtNumeroOrden.focusInEvent = lambda event: self.clear_placeholder_and_reset_style(self.txtNumeroOrden, event)

        #Serial code Test I
        self.txtSerialCode.returnPressed.connect(self.test_1)
        self.lblEnter_VerifyCode.mousePressEvent = self.test_1


        #Firmware version Test 2
        self.Test_2_signal.connect(self.Test_2_GUI_changes)

    
################## CONFIGURATION #############################################
    def show_edit_screen_configuration(self,event):
        self.stackedWidget.setCurrentIndex(13)
        current_config=self.config.get_current_config()

        gateway_port=str(current_config[0])
        RS232_port=str(current_config[1])
        RS485_port=str(current_config[2])
        camera_address=str(current_config[3])
        #camera_port=current_config[4]
        timer=str(current_config[4])
        self.txtGatewayPort.setText(str(gateway_port))
        self.txt232Port.setText(str(RS232_port))
        self.txt485Port.setText(str(RS485_port))
        self.txtCameraAddress.setText(str(camera_address))
        #self.lblTimer.setText(timer)
    

    def show_configuration(self,event):
        self.stackedWidget.setCurrentIndex(12)

        current_config=self.config.get_current_config()

        gateway_port=str(current_config[0])
        RS232_port=str(current_config[1])
        RS485_port=str(current_config[2])
        camera_address=str(current_config[3])
        #camera_port=current_config[4]
        timer=str(current_config[4])
        self.lblGatewayPort.setText(str(gateway_port))
        self.lbl232Port.setText(str(RS232_port))
        self.lbl485Port.setText(str(RS485_port))
        self.lblCameraAddress.setText(str(camera_address))
        self.lblTimer.setText(timer)
        
    def save_configuration(self, event):
        if (self.txtGatewayPort.text() and self.txt232Port.text() and 
            self.txt485Port.text() and self.txtCameraAddress.text()):
            
            # Gateway port
            self.new_gateway_port = self.txtGatewayPort.text()
            search_result = re.search(r'\d+', self.new_gateway_port)
            self.new_gateway_port = search_result.group() if search_result else "1"
            self.gateway_new_port_string = f'"COM{str(self.new_gateway_port)}"'

            # RS232 Port
            self.new_232_port = self.txt232Port.text()
            search_result = re.search(r'\d+', self.new_232_port)
            self.new_232_port = search_result.group() if search_result else "1"
            self.new_232_port_string = f'"COM{str(self.new_232_port)}"'

            # RS485 Port
            self.new_485_port = self.txt485Port.text()
            search_result = re.search(r'\d+', self.new_485_port)
            self.new_485_port = search_result.group() if search_result else "1"
            self.new_485_port_string = f'"COM{str(self.new_485_port)}"'

           
            # Camera Address
            self.new_camera_address = str(self.txtCameraAddress.text())
            # Regular expression to match an IPv4 address
            ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            search_result = re.search(ip_pattern, self.new_camera_address)

            # Fallback to a default IP if no valid IP is found
            if search_result:
                self.new_camera_address = search_result.group()
            else:
                self.new_camera_address = "192.168.1.1"  # Default fallback IP address

            self.new_timer_value = str(self.spinBoxTimer.value())

            self.config.save_new_configuration(self.gateway_new_port_string,self.new_232_port_string,
                                               self.new_485_port_string,self.new_camera_address,
                                               self.new_timer_value)

            self.show_configuration(event)
        else:
            
            print("Por favor, completa todos los campos antes de guardar la configuración.")

            # Set placeholders for empty or invalid fields
            self.set_placeholder_with_style(self.txtGatewayPort, "Texto faltante")
            self.set_placeholder_with_style(self.txt232Port, "Texto faltante")
            self.set_placeholder_with_style(self.txt485Port, "Texto faltante")
            self.set_placeholder_with_style(self.txtCameraAddress, "Texto faltante")
    
    def set_placeholder_with_style(self, widget, placeholder_text):
        if not widget.text():
            widget.setPlaceholderText(placeholder_text)
            widget.setStyleSheet("color: rgb(170, 0, 0);")

    def clear_placeholder_and_reset_style(self, widget, event):
        widget.setPlaceholderText("")
        widget.setStyleSheet("")  # Resets to default style
        super(type(widget), widget).focusInEvent(event)
    
###############################################################

    

    def verify_user_and_ShopOrder(self):
        currentUserId=self.txtNumeroEmpleado.text()
        currentShopOrder=self.txtNumeroOrden.text()

        if currentUserId and currentShopOrder:

            # Verificar si ambos valores son números y cumplen con la longitud requerida
            if re.fullmatch(r'\d{4}', currentUserId) and re.fullmatch(r'\d{6}', currentShopOrder):
                print("Datos válidos obtenidos")

                currentUserId=str(currentUserId)
                self.lblNumeroEmpleado.setText(currentUserId)

                currentShopOrder=str(currentShopOrder)
                self.lblNumeroOrden.setText(currentShopOrder)

                #Show User and Shop order input confirm Screen
                self.stackedWidget.setCurrentIndex(5)
               
            else:
                print("Datos no válidos o no cumplen con los requisitos")

                #Erase textfield information
                self.txtNumeroEmpleado.setText("")
                self.txtNumeroOrden.setText("")

                self.set_placeholder_with_style(self.txtNumeroEmpleado, "Formato invalido")
                self.set_placeholder_with_style(self.txtNumeroOrden, "Formato invalido")

                #Show User and Shop order input 
                #self.stackedWidget.setCurrentIndex(4)
        else:
            print("Informacion de usuario u orden faltante ")           
            self.set_placeholder_with_style(self.txtNumeroEmpleado, "Texto faltante")
            self.set_placeholder_with_style(self.txtNumeroOrden, "Texto faltante")
    
    def confirm_and_save_userId_and_ShopOrder(self,event):

        currentUserId=str(self.lblNumeroEmpleado.text())
        currentShopOrder=str(self.lblNumeroOrden.text())

        self.config.save_new_user_and_shop_info(currentUserId,currentShopOrder)

        #Put information in GUI 
        self.lblCurrentUser.setText(currentUserId)
        self.lblCurrentOrder.setText(currentShopOrder)
        
        #Show first test index screen
        self.stackedWidget.setCurrentIndex(6)
        self.txtSerialCode.setFocus()

    
    def deny_userId_and_ShopOrder(self,event):

        #Erase information in textfields
        self.txtNumeroEmpleado.setText("")
        self.txtNumeroOrden.setText("")
        
        #Show again user input information 
        self.stackedWidget.setCurrentIndex(4)

    def back_to_inicialize_app(self):
        self.stackedWidget.setCurrentIndex(0)

    def inicialize(self,event):
        print("App inicialized")

        print("Obtaining instruments configuration")
        current_config=self.config.get_current_config()

        gateway_port=current_config[0]
        RS232_port=current_config[1]
        RS485_port=current_config[2]
        camera_address=current_config[3]
        camera_port=current_config[4]

        print("Verifiying instruments...")

        print("Verifiying Serial port ")

        self.gateway.open(gateway_port)

        if not self.gateway.is_connected():
            self.stackedWidget.setCurrentIndex(2)
            #return

        self.Rs232 = SerialDevice(port=RS232_port, baudrate=9600, timeout=1)

        if not self.Rs232.connect():
            print("Serial 232 Device NOT connected connected")
            self.stackedWidget.setCurrentIndex(1)
            #return


        self.Rs485 = SerialDevice(port=RS485_port, baudrate=9600, timeout=1)

        if not self.Rs485.connect():
            print("Serial 485 Device NOT connected connected")
            self.stackedWidget.setCurrentIndex(1)
            #return

        #Camera Connection through telnet protocol
        
        self.Camera=TelnetClient(camera_address,camera_port)

        if not self.Camera.connect():
            print("Camera connection Telnet not established")
            self.stackedWidget.setCurrentIndex(3)
            #return

        print("All devices sucessfully conected")  

        #Instrument verification finished

        data = self.config.get_current_user()

        # Verificar si ambos valores son números y cumplen con la longitud requerida
        if re.fullmatch(r'\d{4}', data[0]) and re.fullmatch(r'\d{6}', data[1]):
            print("Datos válidos obtenidos")
            # Aquí puedes continuar con la lógica si los datos son válidos
            currentUserId=str(data[0])
            self.lblCurrentUser.setText(currentUserId)

            currentShopOrder=str(data[1])
            self.lblCurrentOrder.setText(currentShopOrder)
            
            #Show first test index screen
            self.stackedWidget.setCurrentIndex(6)

            self.txtSerialCode.setFocus()
        else:
            print("Datos no válidos o no cumplen con los requisitos")

            #Show User and Shop order input 
            self.stackedWidget.setCurrentIndex(4)
    
    def test_1(self,event=None):
        
        print("Primera prueba")

        #Ejemplo formato codigo serial
        #BQ244423100510013

        serial_code=self.txtSerialCode.text()

        print(f"Codigo introducido: {serial_code}")

         # Evaluar el formato del código serial
        if len(serial_code) == 17 and serial_code[:2].isalpha():
            print("Código serial válido:", serial_code)
            # Aquí puedes añadir más lógica para manejar un código válido

            self.lblVerifySerialCode.setText("Codigo capturado")
            self.lblVerifySerialCode.setStyleSheet("color: green;")
            self.txtSerialCode.setEnabled(False)

            self.test.result_T1(str(serial_code))

            time.sleep(1)
            #Continue with Test2
            self.test_2()

        else:
            print("Código serial no válido")
            # Aquí puedes añadir lógica para manejar un código no válido
            self.lblVerifySerialCode.setText("Codigo invalido")
            self.lblVerifySerialCode.setStyleSheet("color: red;")

            # Opcional: limpiar el campo de texto después de la evaluación
            self.txtSerialCode.clear()


    def test_2(self):
        print("Segunda prueba")

        #Read register to verify HMI presence in Fixture

        

        '''
        daemon=True: Esto indica que el hilo será un "hilo daemon", 
        lo que significa que el hilo se cerrará automáticamente 
        cuando el programa principal termine. 
        Si no utilizas daemon=True, 
        deberías manejar el cierre del hilo manualmente.'''
        '''# Crear un hilo para leer la bobina sin bloquear el hilo principal
        hilo_bobina = threading.Thread(target=self.check_handheld_status,daemon=True)
        # Iniciar el hilo
        hilo_bobina.start()'''

        print("Enabling command mode in HMI ")

        self.Rs485.send_command("FF00FFA50060100D04D05101010249")

        print("Obtaining firmware version ")
        firmware_version=str(self.Rs485.send_command("FF00FFA50060100D03D05600024B"))

        print(f"Firmware response:{firmware_version}")

        if firmware_version:
            self.txtFirmware.setText(firmware_version)

            self.lblVerifyFirmware.setText("Firmware capturado")
            self.lblVerifyFirmware.setStyleSheet("color: green;")

            # Crear un QTimer para emitir la señal después de 3 segundos
            QTimer.singleShot(3000, lambda: self.Test_2_signal.emit())

            self.test.result_T2(firmware_version)


       
        else:
            self.lblVerifyFirmware.setText("Firmware NO capturado")
            self.lblVerifySerialCode.setStyleSheet("color: red;")


    def Test_2_GUI_changes(self):
            #Third Test
            self.stackedWidget.setCurrentIndex(7)  

    def check_handheld_status(self):
         while True:
            # Leer la bobina y procesar su estado
            handheld_status=self.gateway.read_coil(1)
            if handheld_status:
                print("Bobina detectada")

            # Esperar un poco antes de volver a leer (por ejemplo, cada 1 segundo)
            time.sleep(.5)





    def update_table_register(self, Barcode,Result,response,program,id):
        # Codes
        Etiqueta = str(Barcode)
        
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%H:%M:%S_%d-%m-%y")

        formatted_time = current_datetime.strftime("%H:%M:%S")

        Current_date = str(formatted_datetime)

        Current_time=str(formatted_time)
       
        # Assembling the register
        # Table register
        self.register = {"ID":id,"Etiqueta": Etiqueta,"Programa": program,"Resultado": Result, "Hora": Current_time}
      
        # Logic to verify number of table registers and only show 9 registers 
        table_registers = self.ResultsTable.rowCount()
        if table_registers > 9:
            self.ResultsTable.removeRow(9)
  
        # Register insertion at top of table
        row = 0  # Insert the new register at the top of the table
        row_count = self.ResultsTable.rowCount()  # Obtener el número de filas actual en la tabla
        self.ResultsTable.insertRow(row)  # Insertar una nueva fila en la tabla

        col = 0  # Columna inicial para insertar valores

        for key, value in self.register.items():
            item = QtWidgets.QTableWidgetItem(str(value))  # Crear un QTableWidgetItem con el valor del diccionario
            item.setTextAlignment(Qt.AlignCenter)  # Centrar el texto en la celda
            self.ResultsTable.setItem(row, col, item)  # Establecer el QTableWidgetItem en la celda correspondiente
            col += 1  # Mover a la siguiente columna para el próximo valor del diccionario
       
        self.csv_register = {"ID":id,"Etiqueta": Etiqueta,"Programa":program,"Resultado": Result,"Respuesta sensor":response, "Operador":self.complete_name,"Fecha":Current_date}
        
        # Call csv register add function 
        self.csv_registers_add(self.csv_register)



if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()

    app.exec_()