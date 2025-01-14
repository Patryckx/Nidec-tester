from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt

from PyQt5.QtCore import QTimer

from ui.Application import Ui_MainWindow as mainApplication

#Instruments
from utilities.DAQ.DAQ import FX3U
from utilities.Telnet_lib.telnet import TelnetClient
from utilities.PySerial.PySerial_lib import SerialDevice
from utilities.Configuration.Config import Configuration


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
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.connect_signals()
    

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

    

    def get_userinfo(self,name,apellidos):
        self.user_name = name
        self.user_apellidos = apellidos

        self.complete_name=(f"{self.user_name} {self.user_apellidos}")


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

    #Show error events
    def back_to_inicialize_app(self):
        self.stackedWidget.setCurrentIndex(0)

    def show_edit_screen_configuration(self,event):
        self.stackedWidget.setCurrentIndex(11)
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
        self.stackedWidget.setCurrentIndex(10)

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





if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()

    app.exec_()