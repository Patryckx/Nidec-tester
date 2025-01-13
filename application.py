from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt

from PyQt5.QtCore import QTimer

from ui.Application import Ui_MainWindow as mainApplication

from utilities.DAQ.DAQ import FX3U


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

        self.session_app=Session()

        # Space bar function initialized flag 
        self.initialized_flag = None'''

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
        pass
        '''
        if event.key() == Qt.Key_Space and self.initialized_flag is None:
            # Initialize application pressing Space Bar
            print("space bar pressed")
            self.inicialize(event)

       if event.key() == Qt.Key_Return and self.initialized_flag ==True :  
            # Aquí se ejecuta la acción al presionar Enter
            print("Se presionó Enter")
            #self.get_validate_Mspec()
            self.Validate_Barcode_and_response(event)'''
  

    def connect_signals(self):
        '''self.lblstart.mousePressEvent = self.inicialize
        self.lblconfig.mousePressEvent = self.open_config
        self.lblstop.mousePressEvent = self.stop_scanning
        self.lblEnter.mousePressEvent=self.Validate_Barcode_and_response

        #►Enter Key to execute code validation
        self.txtCode.returnPressed.connect(lambda: self.Validate_Barcode_and_response(None))

        self.lblShowSession.mousePressEvent=self.showSessionApp'''

        pass



if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()

    app.exec_()