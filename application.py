from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton
from PyQt5 import QtCore, QtGui, QtWidgets
from ui.Application import Ui_MainWindow as mainApplication
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
#Instruments
from utilities.DAQ.DAQ import FX3U
from utilities.Telnet_lib.telnet import TelnetClient
from utilities.PySerial.PySerial_lib import SerialDevice
from utilities.Configuration.Config import Configuration
from utilities.Tests.Tests import Manage_tests

from PyQt5.QtCore import Qt
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

from PyQt5.QtCore import QThread, pyqtSignal, Qt

from PyQt5.QtCore import QThread, pyqtSignal
import time

class Palmswitch_inicialize_Thread(QThread):
    # Señales para comunicar con el hilo principal
    inicialize_signal = pyqtSignal()  # Señal cuando el monitoreo detecta un False y detiene el hilo
    failed_inicialize_signal = pyqtSignal()  # Señal cuando ambas verificaciones son exitosas
    stop_monitoring_palm_button_signal = pyqtSignal()  # Señal para indicar que el hilo se detuvo

    def __init__(self, gateway, parent=None):
        super(Palmswitch_inicialize_Thread, self).__init__(parent)
        self.gateway = gateway
        self._is_running = True  # Bandera para controlar el hilo
        
    def run(self):
        attempts = 0
        max_attempts = 15

        while attempts < max_attempts and self._is_running:
            HMI_in_position = self.gateway.read_coil(17)
            print(HMI_in_position)

            if HMI_in_position:
                self.inicialize_signal.emit()
                self.stop_monitoring_palm_button_signal.emit()
                return  # Salimos del bucle si se detecta la bobina

            attempts += 1
            self.msleep(1000)  # Evita bloquear la GUI

        self.failed_inicialize_signal.emit()
        self.stop_monitoring_palm_button_signal.emit()

    def stop_monithoring_palm_button_thread(self):
        print("Monitoreo detenido.")
        self._is_running = False
        self.quit()  # Detiene el hilo sin bloquear
        self.wait()


class Test3Thread(QThread):
    update_led_signal = pyqtSignal(dict)  # Señal para actualizar LEDs
    test_finished_signal = pyqtSignal(str,dict)  # Señal para actualizar el resultado de la prueba

    def __init__(self, rs485, camera, led_program, parent=None):
        super(Test3Thread, self).__init__(parent)
        self.Rs485 = rs485
        self.Camera = camera
        self.led_program = led_program

    def run(self):
        print("Tercera prueba")
        print("Encendiendo todos los LEDS")

        self.Rs485.send_command("FF00FFA50060100D05D05B0203FF0356")

        # Enviar comandos a la cámara
        raw_change_program = 'PW,'
        change_program = raw_change_program + self.led_program
        self.Camera.send_data(change_program)
        #time.sleep(1)
        '''#elf.Camera.send_data('T2')
        self.Camera.send_data('T2')

        # Leer la respuesta de la cámara
        results = self.Camera.read_data()
        resultados_herramientas = self.procesar_respuesta(results)
        print(resultados_herramientas)'''

        # Limpiar el buffer antes de realizar el disparo
        self.Camera.read_and_clear_buffer()

        # Realizar el disparo y leer la respuesta
        self.Camera.send_data('T2')
        time.sleep(0.5)  # Esperar un breve momento
        results = self.Camera.read_data()

        resultados_herramientas = self.procesar_respuesta(results)
        print(resultados_herramientas)

        # Determinar si la prueba pasó o falló
        test_3_results = "FAIL" if "NG" in results else "PASS"

        # Emitir señales para actualizar la interfaz
        self.update_led_signal.emit(resultados_herramientas)
        self.test_finished_signal.emit(test_3_results,resultados_herramientas)

    def procesar_respuesta(self, respuesta):
        resultados = {}
        try:
            partes = respuesta.split(',')
            for i in range(3, len(partes), 3):
                if i + 1 < len(partes):
                    numero = int(partes[i].lstrip('0'))
                    resultados[numero] = 1 if partes[i + 1] == "OK" else 0
        except Exception as e:
            print(f"Error al procesar la respuesta: {e}")
        return resultados


class Test4Thread(QThread):
    update_lcd_signal = pyqtSignal(dict)  # Señal para actualizar los LCDs
    test_finished_signal = pyqtSignal(str,dict)  # Señal para actualizar el resultado de la prueba

    def __init__(self, rs485, camera, ocr_program, parent=None):
        super(Test4Thread, self).__init__(parent)
        self.Rs485 = rs485
        self.Camera = camera
        self.ocr_program = ocr_program

    def run(self):
        print("Prueba 4")
        print("Encendiendo pantalla LCD 100%")
        self.Rs485.send_command("FF00FFA50060100D04D05C016402B7")
        
        print("Encendiendo todos los Segmentos LCDs")
        print("Imprimiendo todos los segmentos con 8 ochos")
        self.Rs485.send_command("FF00FFA50060100D07D05D0438383838033A")
        
        print("Imprimiendo todos los iconos LCD (AM)")
        self.Rs485.send_command("FF00FFA50060100D04D05E013F0294")

        # Enviar comandos a la cámara
        raw_change_program = 'PW,'
        change_program = raw_change_program + self.ocr_program
        self.Camera.send_data(change_program)

        # Limpiar el buffer antes de realizar el disparo
        self.Camera.read_and_clear_buffer()

        # Realizar el disparo y leer la respuesta
        self.Camera.send_data('T2')
        time.sleep(0.5)  # Esperar un breve momento
        results = self.Camera.read_data()

        resultados_herramientas = self.procesar_respuesta(results)
        print(resultados_herramientas)
        
        test_4_results = "FAIL" if "NG" in results else "PASS"
      
        # Emitir señales para actualizar la interfaz
        self.update_lcd_signal.emit(resultados_herramientas)
        self.test_finished_signal.emit(test_4_results,resultados_herramientas)

    def procesar_respuesta(self, respuesta):
        resultados = {}
        try:
            partes = respuesta.split(',')
            for i in range(3, len(partes), 3):
                if i + 1 < len(partes):
                    try:
                        numero = int(partes[i].lstrip('0'))  # Intentar convertir el número
                    except ValueError:
                        continue  # Si no es un número, ignorar esta parte y continuar

                    estado = 1 if partes[i + 1] == "OK" else 0  # Verificar si el estado es OK o NG
                    if 1 <= numero <= 10:  # Solo agregar los números entre 1 y 10
                        resultados[numero] = estado
        except Exception as e:
            print(f"Error al procesar la respuesta: {e}")
        return resultados


class MonitorButtonsThread(QThread):
    # Definir señales para la comunicación con el hilo principal
    button_detected_signal = pyqtSignal(str)
    update_button_signal = pyqtSignal(str, str,bool)
    test_finished_signal = pyqtSignal(bool,dict)

    def __init__(self, buttons_order, button_actuators_order, rs485, gateway, parent=None):
        super(MonitorButtonsThread, self).__init__(parent)
        self.buttons_order = buttons_order
        self.button_actuators_order = button_actuators_order
        self.rs485 = rs485
        self.gateway = gateway  # Modbus para controlar bobinas

        self.pending_buttons_list = list(self.buttons_order.values())
        self.pending_buttons_index = [index + 1 for index, _ in enumerate(self.pending_buttons_list)]
        self.pending_button_actuator_list = list(self.button_actuators_order.values())
        self.running = True
        
        # Inicializar el diccionario con claves de 1 a n, con valores en None
        self.button_results_dict = {i + 1: None for i in range(len(self.pending_buttons_list))}
        print(self.button_results_dict)
        #Clear results dictionary button
        self.button_results_dict.clear()

    def run(self):
        while self.pending_buttons_list and self.pending_button_actuator_list and self.running:
            current_coil = self.pending_button_actuator_list[0]  # Obtener la bobina actual
            print(f"Activando bobina {current_coil}")
            
            try:
                self.gateway.write_coil(current_coil, True)  # Encender bobina
            except Exception as e:
                print(f"Ocurrió un error al encender la bobina: {e}")
                
            attempts = 0  # Contador de intentos
            max_attempts = 5
            detected = False

            #Flag to check if the test failed
            fail_on_button_test=False

            while attempts < max_attempts and self.running:
                response = self.rs485.send_command("FF00FFA50060100D04D05101000248")
                print(response)
                
                hex_value = response[24:26]  # Extrae el valor hexadecimal relevante
                
                if hex_value == self.pending_buttons_list[0]:
                    print(f"Botón detectado: {hex_value}")
                    current_index = self.pending_buttons_index.pop(0)
                    button = f"lblButton{current_index}"
                    button_input = f"lblButtonInput{current_index}"

                    #Guardar resultado en el diccionario
                    self.button_results_dict[current_index] = 1
                    
                    # Emitir señal para actualizar la GUI
                    self.update_button_signal.emit(button, button_input,True)
                    detected = True
                    break  # Salir del bucle de intentos
                
                attempts += 1
                print(f"Intento {attempts} de {max_attempts} para detectar el botón.")

            # Apagar la bobina y procesar el resultado
            print(f"Desactivando bobina {current_coil}")
            try:
                self.gateway.write_coil(current_coil, False)  # Apagar bobina
            except Exception as e:
                print(f"Ocurrió un error al desactivar la bobina: {e}")

            if not detected:
                print("Botón no detectado tras 5 intentos.")
                current_index = self.pending_buttons_index.pop(0)
                button = f"lblButton{current_index}"
                button_input = f"lblButtonInput{current_index}"
                self.update_button_signal.emit(button, button_input,False)

                #Guardar resultado en el diccionario
                self.button_results_dict[current_index] = 0

                fail_on_button_test=True

            
            # Eliminar el botón de la lista
            self.pending_buttons_list.pop(0)
            self.pending_button_actuator_list.pop(0)
            
            if not self.pending_buttons_list:
                print("Todos los botones han sido procesados.")
                self.test_finished_signal.emit(fail_on_button_test,self.button_results_dict)

                
                break

    def stop(self):
        self.running = False

class MonitorDigitalEntrances(QThread):
    # Definir señales para la comunicación con el hilo principal
    digital_input_detected_signal = pyqtSignal(str)
    update_digital_input_signal = pyqtSignal(str, str)
    test_6_finished_signal = pyqtSignal()

    def __init__(self, digital_input_order, digital_actuators_order, rs485, gateway, parent=None):
        super(MonitorDigitalEntrances, self).__init__(parent)
        self.digital_input_order = digital_input_order
        self.digital_actuators_order = digital_actuators_order
        self.rs485 = rs485
        self.gateway = gateway  # Modbus para controlar bobinas

        # Listas pendientes
        self.pending_digital_list = list(self.digital_input_order.values())
        self.pending_digital_index = [index + 1 for index, _ in enumerate(self.pending_digital_list)]
        self.pending_actuator_list = list(self.digital_actuators_order.values())

        self.digital_entrances_thread_isrunning = True

    def run(self):
        while self.pending_digital_list and self.pending_actuator_list and self.digital_entrances_thread_isrunning:
            current_coil = self.pending_actuator_list[0]  # Obtener la bobina actual
            attempts = 0  # Contador de intentos
            max_attempts = 5
            
            print(f"Activando bobina {current_coil}")
            try:
                self.gateway.write_coil(current_coil, True)  # Encender bobina
            except Exception as e:
                print(f"Ocurrio un error al encender la bobina: {e}")
                
            while attempts < max_attempts:
                response = self.rs485.send_command("FF00FFA50060100D04D05101000248")  # Obtener respuesta
                print(response)
                hex_value = response[26:28]  # Extrae el valor hexadecimal relevante
                
                if hex_value == self.pending_digital_list[0]:
                    print(f"Entrada detectada: {hex_value}")
                    current_index = self.pending_digital_index.pop(0)
                    print(current_index)
                    digital = f"lblDigital{current_index}"
                    digital_input = f"lblDigitalInput{current_index}"

                    # Emitir una señal para actualizar la GUI en el hilo principal
                    self.update_digital_input_signal.emit(digital, digital_input)
                    break
                
                attempts += 1
                print(f"Intento {attempts} de {max_attempts} para detectar la entrada")
            
            print(f"Desactivando bobina {current_coil}")
            try:
                self.gateway.write_coil(current_coil, False)  # Apagar bobina
            except Exception as e:
                print(f"Ocurrio un error al desactivar la bobina: {e}")

            if attempts >= max_attempts:
                print(f"Entrada no detectada después de {max_attempts} intentos.")
            
            # Eliminar elementos procesados
            self.pending_digital_list.pop(0)
            self.pending_actuator_list.pop(0)

            if not self.pending_digital_list:
                print("Todas las señales han sido capturadas.")
                self.test_6_finished_signal.emit()  # Emitir señal para indicar que la prueba ha finalizado
                break

    def stop(self):
        self.digital_entrances_thread_isrunning = False


class MainWindow(QMainWindow, mainApplication):

#Signals 

    Test_1_signal = pyqtSignal()

    Test_2_signal = pyqtSignal()

    Test_3_signal = pyqtSignal()

    Test_4_signal=pyqtSignal()

    Test_5_signal=pyqtSignal()

    Test_6_signal=pyqtSignal()

    Test_resume_signal=pyqtSignal()

    failed_firmware_version_signal=pyqtSignal()

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.connect_signals()

        # Eliminar la barra de título y los botones de control
        self.setWindowFlags(Qt.FramelessWindowHint)
        #self.setWindowState(Qt.WindowFullScreen)  # Pantalla completa
        self.setMouseTracking(True)  # Seguimiento del mouse
        self._startPos = None  # Para guardar la posición inicial del mouse
        #Preparar tabla ajustar tabla a columnas
        #self.ResultsTable.horizontalHeader().setSectionResizeMode(1)
        # Formato a tabla
        headers = ['Codigo','Firmware','LED', 'LCDS','Botones','Entradas','Fecha' ]
        # Configuración de la tabla
        self.ResultsTable.setColumnCount(len(headers))
        self.ResultsTable.setHorizontalHeaderLabels(headers)

        # Ajustar el ancho de las columnas
        self.ResultsTable.setColumnWidth(headers.index('Codigo'), 120)
        self.ResultsTable.setColumnWidth(headers.index('Firmware'), 120)
        self.ResultsTable.setColumnWidth(headers.index('LED'), 120)
        self.ResultsTable.setColumnWidth(headers.index('LCDS'), 120)
        self.ResultsTable.setColumnWidth(headers.index('Botones'), 120)
        self.ResultsTable.setColumnWidth(headers.index('Entradas'), 120)
        self.ResultsTable.setColumnWidth(headers.index('Fecha'), 300)

        # Actualizar la vista
        self.ResultsTable.update()

        #Instance config class
        self.config=Configuration()

        self.gateway=FX3U()

        self.test=Manage_tests()

        # Space bar function initialized flag 
        self.initialized_flag = False
        #Flag to not add register if timer goes up
        self.dont_add_register=None
        
        #Serial Code scanned flag
        self.serial_code_captured=None


        #Timer test 
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)  # Conectar la señal timeout a la función
        self.remaining_time = 0  # Variable para almacenar el tiempo restante

        # Lista para almacenar los hilos activos
        self.threads = []
        
        #Disable stop button 
        self.btnLogout.setEnabled(False)


        # Asegurar que la ventana pueda recibir eventos de teclado
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
    
    ############# TIMER #####################

    def start_timer_clicked(self):
        """Inicia el temporizador con un valor inicial."""
        initial_time = 90  # Puedes cambiar este valor o obtenerlo de la configuración
        self.start_timer(initial_time)
    
    def start_timer(self, initial_time):
        """Inicia el temporizador con el tiempo dado en segundos."""
        self.remaining_time = initial_time
        self.update_timer_display()  # Actualiza inmediatamente el display con el tiempo inicial
        self.timer.start(1000)  # Comienza el temporizador para emitir cada 1000 ms (1 segundo)

    def update_timer(self):
        """Actualiza el temporizador cada segundo."""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_timer_display()
        else:
            self.timer.stop()
            self.timer_finished()  # Llama a la función cuando el temporizador llega a cero

    def update_timer_display(self):
        """Actualiza la etiqueta del temporizador."""
        minutes, seconds = divmod(self.remaining_time, 60)
        formatted_time = f"{minutes:02}:{seconds:02}"
        self.lbltimer.setText(formatted_time)

    def timer_finished(self):
        """Función que se ejecuta cuando el temporizador llega a cero."""
        print("Timer finished!")

        #Stop buttons thread

        try:

            self.monitor_buttons_thread.stop()

            self.monitor_buttons_thread.quit()
            self.monitor_buttons_thread.wait()
        except Exception as e :
            print("Error al detener el hilo de monitoreo de botones")

        try:
            self.monitor_digital_inputs_thread.stop()
            self.monitor_digital_inputs_thread.quit()
            self.monitor_digital_inputs_thread.wait()
        except Exception as e:
            print("Error al detener el hilo de monitoreo de entradas digitales")


        

        print("Apagando bobina para alimentar 5V a hmi")

        try: 
            self.gateway.write_coil(0,False)
        except Exception as e:
            print(f"Ha ocurrido un error al apagar la bobina 5v : {e}")

        self.housekeeping_gateway()


        #Stoping monithoring thread HMI 

        #self.monitor_thread.stop_monitoring_signal.emit()

        print("Enciendiendo pantalla LCD 100%")

        self.Rs485.send_command("FF00FFA50060100D04D05C016402B7")

        #putting back HMI in monitor mode
        self.Rs485.send_command("FF00FFA50060100D04D05101000248")

        #Flag to not add register if test are not performed
        self.dont_add_register=True

        self.btnPrueba3.setStyleSheet("background-color: red;")
        self.btnPrueba4.setStyleSheet("background-color: red;")
        self.btnPrueba5.setStyleSheet("background-color: red;")
        self.btnPrueba6.setStyleSheet("background-color: red;")

        self.btnResultados.setStyleSheet("background-color: red;")
        self.Test_6_signal.emit()
        

        self.stop_all_threads()
        

    def stop_all_threads(self):
        """Detiene todos los hilos activos."""
        print("Stopping all threads...")
        for thread in self.threads:
            if thread.is_alive():
                # Aquí podrías implementar una señal o flag para detener hilos seguros
                print(f"Stopping thread {thread.name}")
        self.threads.clear()  # Limpia la lista de hilos

    ################# APP FUNCTIONS ########################################
        

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
            """ Detectar la barra espaciadora """
            if event.key() == Qt.Key_Space:
                print("Barra espaciadora presionada")
                if not self.initialized_flag:
                    self.initialized_flag = True
                    self.inicialize(event)

    def close(self, event):
        reply = QMessageBox.question(
            self,
            'Confirmar cierre',
            '¿Estás seguro de que quieres cerrar la aplicación?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
            QApplication.quit()

            try:
                self.housekeeping_gateway()
            except Exception as e:
                print("Error al apagar bobinas")
        else:
            event.ignore()
    def minimize_window(self,event):
        #Minimize window app
        self.showMinimized()
       
  

    def connect_signals(self):

        self.lblClose.mousePressEvent=self.close

        self.lblMinize.mousePressEvent=self.minimize_window

        self.lblinicialize.mousePressEvent = self.inicialize

        self.btnLogout.clicked.connect(self.log_out)

        self.btnTrazabilidad.clicked.connect(self.traceability)

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
        self.txtNumeroEmpleado.returnPressed.connect(self.txtNumeroOrden.setFocus)
        self.txtNumeroOrden.returnPressed.connect(self.verify_user_and_ShopOrder)

        self.txtNumeroEmpleado.focusInEvent = lambda event: self.clear_placeholder_and_reset_style(self.txtNumeroEmpleado, event)
        self.txtNumeroOrden.focusInEvent = lambda event: self.clear_placeholder_and_reset_style(self.txtNumeroOrden, event)

        #Serial code Test I
        self.txtSerialCode.returnPressed.connect(self.test1_verify_serial_code)
        self.lblEnter_VerifyCode.mousePressEvent = self.test_1

        self.txtQrcode.returnPressed.connect(self.test_1)

        self.btnPrueba1.clicked.connect(self.test_inicialize)

        #HMI verification 
        
        # Conectar señales
        
        self.btnHMIRemoved.clicked.connect(self.cancel_remaining_test_and_functions)

        #Test 1 timer 

        self.Test_1_signal.connect(self.test_2)

        #Firmware version Test 2
        self.Test_2_signal.connect(self.Test_2_GUI_changes)
        self.failed_firmware_version_signal.connect(self.test_2_failed_firmware_version_response)


        #LEDs test 3
        #self.lblConfirmLeds.mousePressEvent = self.manual_test_3_verification
        #self.lblDenyLeds.mousePressEvent=self.deny_test_3_verification
        self.Test_3_signal.connect(self.Test_3_GUI_changes)

        #LCD Test 4

        #self.lblConfirmLCDS.mousePressEvent=self.manual_test_4_verification
        #self.lblDenyLCDS.mousePressEvent=self.deny_test_4_verification
        self.Test_4_signal.connect(self.Test_4_GUI_changes)

        #Test 5 
        self.Test_5_signal.connect(self.Test_5_GUI_changes)

        self.lblCancelTestButtons.mousePressEvent=self.cancel_remaining_test_and_functions

        #Test 6
        self.Test_6_signal.connect(self.Test_6_GUI_changes)

        #Resume test

        self.Test_resume_signal.connect(self.Test_resume_GUI_changes)



    
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
        timer=str(current_config[5])
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
    
###################  lOGIN USER AND SHOP ORDER    ############################################

    

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

                self.txtNumeroEmpleado.setFocus()

                #Show User and Shop order input 
                #self.stackedWidget.setCurrentIndex(4)
        else:
            print("Informacion de usuario u orden faltante ")           
            self.set_placeholder_with_style(self.txtNumeroEmpleado, "Texto faltante")
            self.set_placeholder_with_style(self.txtNumeroOrden, "Texto faltante")

            self.txtNumeroEmpleado.setFocus()

    
    def confirm_and_save_userId_and_ShopOrder(self,event):

        currentUserId=str(self.lblNumeroEmpleado.text())
        currentShopOrder=str(self.lblNumeroOrden.text())

        self.config.save_new_user_and_shop_info(currentUserId,currentShopOrder)

        #Put information in GUI 
        self.lblCurrentUser.setText(currentUserId)
        self.lblCurrentOrder.setText(currentShopOrder)
        
        #Show first test index screen
        self.stackedWidget.setCurrentIndex(6)

        #Enable log out button 
        self.btnLogout.setEnabled(True)
        self.btnInicializar.setEnabled(False)
        self.btnConfiguracion.setEnabled(False)

        self.btnPrueba1.setEnabled(True)
        self.btnPrueba1.setStyleSheet("background-color: rgb(36, 146, 255);")

        self.txtSerialCode.setFocus()

    
    def deny_userId_and_ShopOrder(self,event):

        #Erase information in textfields
        self.txtNumeroEmpleado.setText("")
        self.txtNumeroOrden.setText("")
        
        #Show again user input information 
        self.stackedWidget.setCurrentIndex(4)

    def log_out(self):            

        print("Cerrando sesion actual")

        reply = QMessageBox.question(
            self,
            'Cerrar sesion',
            '¿Estás seguro de que quieres cerrar la sesion actual',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            
            #Erase current session info
            self.config.erase_user_and_shop_info()

            #Show again first screen app
            self.stackedWidget.setCurrentIndex(0)

            self.btnLogout.setEnabled(False)

            self.btnPrueba1.setEnabled(False)
            self.btnPrueba1.setStyleSheet("background-color: ;")

            #Disable inicialize button
            self.btnInicializar.setEnabled(True)
            self.btnConfiguracion.setEnabled(True)

            #Clear txtfields
            self.txtNumeroEmpleado.setText("")
            self.txtNumeroOrden.setText("")


            self.disconnect_all_devices()

            self.lblCurrentUser.setText("")
            self.lblCurrentOrder.setText("")

            #Restore inicialized app flag
            self.initialized_flag=False


        else:
            pass

    def disconnect_all_devices(self):
        self.gateway.close()
        self.Rs232.disconnect()
        self.Rs485.disconnect()
        self.Camera.close_connection()



    ################ INICIALIZE  #################################

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
        self.timer_value = int(current_config[5])  # Asegúrate de convertir el valor a entero
        self.led_program=current_config[6]
        self.ocr_program=current_config[7]


        # Convertir segundos a minutos y segundos
        minutes, seconds = divmod(  self.timer_value, 60)
        self.formatted_timer_time = f"{minutes:02}:{seconds:02}"  # Formato MM:SS

        self.lbltimer.setText(self.formatted_timer_time)

        print("Verifiying instruments...")

        print("Verifiying Serial port ")

        self.gateway.open(gateway_port)

        if not self.gateway.is_connected():
            self.stackedWidget.setCurrentIndex(2)
            return

        #Housekeeping registers gateway
        self.housekeeping_gateway()

        self.Rs232 = SerialDevice(port=RS232_port, baudrate=9600, timeout=1)

        if not self.Rs232.connect():
            print("Serial 232 Device NOT connected connected")
            self.stackedWidget.setCurrentIndex(1)
            #return


        self.Rs485 = SerialDevice(port=RS485_port, baudrate=9600, timeout=1)

        if not self.Rs485.connect():
            print("Serial 485 Device NOT connected connected")
            self.stackedWidget.setCurrentIndex(1)
            return

        #Camera Connection through telnet protocol
        
        self.Camera=TelnetClient(camera_address,camera_port)

        if not self.Camera.connect():
            print("Camera connection Telnet not established")
            self.stackedWidget.setCurrentIndex(3)
            return

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

            #Disable inicialize button
            self.btnInicializar.setEnabled(False)
            
            self.btnConfiguracion.setEnabled(False)


            #Show first test index screen
            self.stackedWidget.setCurrentIndex(6)

            #Enable log out button 
            self.btnLogout.setEnabled(True)
            
            self.btnPrueba1.setEnabled(True)
            
            self.btnPrueba1.setStyleSheet("background-color: rgb(36, 146, 255);")

            self.txtSerialCode.setFocus()
        else:
            print("Datos no válidos o no cumplen con los requisitos")

            #Show User and Shop order input 
            self.stackedWidget.setCurrentIndex(4)
            self.txtNumeroEmpleado.setFocus()

    def housekeeping_gateway(self):
        '''Function to turn off importar register coils every time the app inicializes'''
        print("Apagando bobina para alimentar 5V a hmi")
        try: 
            self.gateway.write_coil(0,False)
        except Exception as e:
            print(f"Ha ocurrido un error al apagar la bobina 5v : {e}")

        #activating actuator box 

        try: 
            self.gateway.write_coil(1,False)
        except Exception as e:
            print(f"Ha ocurrido un error al activar el piston de la caja de actuadores : {e}")

        #Acuators buttons
        
        try: 
            self.gateway.write_coil(2,False)
            self.gateway.write_coil(3,False)
            self.gateway.write_coil(4,False)
            self.gateway.write_coil(5,False)
            self.gateway.write_coil(6,False)
            self.gateway.write_coil(7,False)
            self.gateway.write_coil(8,False)
            self.gateway.write_coil(9,False)



        except Exception as e:
            print(f"Ha ocurrido un error al activar el piston de la caja de actuadores : {e}")
        
           
        try: 
            self.gateway.write_coil(12,False)
            self.gateway.write_coil(13,False)
            self.gateway.write_coil(14,False)
            self.gateway.write_coil(15,False)



        except Exception as e:
            print(f"Ha ocurrido un error al activar el piston de la caja de actuadores : {e}")

        

    def test_inicialize(self):

        #Show first test screen
        self.stackedWidget.setCurrentIndex(6)

    def test1_verify_serial_code(self):
        print("Primera prueba verificando codigo serial")

        #Ejemplo formato codigo serial
        #BQ244423100510013

        self.serial_code=self.txtSerialCode.text()

        print(f"Codigo introducido: {self.serial_code}")

         # Evaluar el formato del código serial
        #if len(serial_code) == 17 and serial_code[:2].isalpha():
        if  self.serial_code[:2].isalpha():
            print("Código serial válido:", self.serial_code)
            # Aquí puedes añadir más lógica para manejar un código válido
            self.serial_code_captured=True

            self.lblVerifySerialCode.setStyleSheet("color: blue;")

            self.lblVerifySerialCode.setText("Por favor introduzca el codigo QR")

            self.txtSerialCode.setEnabled(False)
            
            self.txtQrcode.setFocus()

        else:
            print("Código serial no válido")
            # Aquí puedes añadir lógica para manejar un código no válido
            self.lblVerifySerialCode.setText("Codigo invalido")
            self.lblVerifySerialCode.setStyleSheet("color: red;")
            #Test Button 
            self.btnPrueba1.setStyleSheet("background-color: red;")
            self.serial_code_captured=False


            # Opcional: limpiar el campo de texto después de la evaluación
            self.txtSerialCode.clear()
            self.txtSerialCode.setFocus()


        

    
    def test_1(self,event=None):
        
        print("Primera prueba codigo QR")

        #Ejemplo formato codigo serial
        #BQ244423100510013

        self.qrcode=self.txtQrcode.text()

        #if self.qrcode[:2].isalpha() and self.serial_code_captured:
        if self.qrcode  and self.serial_code_captured:
            #Test Button 
            self.btnPrueba1.setStyleSheet("background-color: green;")

            #Disable app function once the test is inicalized
            self.lblVerifySerialCode.setStyleSheet("color: green;")

            self.lblVerifySerialCode.setText("Codigos capturados")

            self.txtQrcode.setEnabled(False)


            self.btnLogout.setEnabled(False)
            self.btnTrazabilidad.setEnabled(False)

            self.btnPrueba1.setEnabled(False)

            self.start_timer( self.timer_value)

            self.test.result_T1(str(self.serial_code),str(self.qrcode))

            self.lblRequestHMI.setText("Favor de posicionar el HMI en el nido y pulsar las botoneras")

            Palmswitch_inicialize_Thread
            self.lblRequestHMI.setStyleSheet("color: #00aaff;")

            # Crear el objeto del hilo
            self.inicialize_thread = Palmswitch_inicialize_Thread(self.gateway)
            self.inicialize_thread.inicialize_signal.connect(self.detected_palm_button)
            self.inicialize_thread.failed_inicialize_signal.connect(self.failed_palm_button_signal)
            self.inicialize_thread.stop_monitoring_palm_button_signal.connect(self.inicialize_thread.stop_monithoring_palm_button_thread)

            # Iniciar el hilo
            self.inicialize_thread.start()
            


            time.sleep(1)
            #Continue with Test2
            #self.hmi_in_position_verification()
            #Proceed with test 2

            # Crear un QTimer para emitir la señal después de 3 segundos
            #QTimer.singleShot(15000, lambda: self.Test_1_signal.emit())
            #QTimer.singleShot(3000, lambda: self.Test_1_signal.emit())
            #self.test_2()

        else:
            print("Código serial no válido")
            # Aquí puedes añadir lógica para manejar un código no válido
            self.lblVerifySerialCode.setText("Codigo(s) invalido o faltante")
            self.lblVerifySerialCode.setStyleSheet("color: red;")
            #Test Button 
            self.btnPrueba1.setStyleSheet("background-color: red;")

            # Opcional: limpiar el campo de texto después de la evaluación
            self.txtSerialCode.clear()
            self.txtQrcode.clear()

            self.txtSerialCode.setFocus()

            self.txtSerialCode.setEnabled(True)
            self.txtQrcode.setEnabled(True)




            




############# HMI IN POSITION VERIFICATION ######################################

    def cancel_remaining_test_and_functions(self,event=None):

        #Stop monitor buttons thread 

        self.housekeeping_gateway()

        try:

            self.monitor_buttons_thread.stop()

            self.monitor_buttons_thread.quit()
            self.monitor_buttons_thread.wait()
        except Exception as e :
            print("Error al detener el hilo de monitoreo de botones")

        try:
            self.monitor_digital_inputs_thread.stop()
            self.monitor_digital_inputs_thread.quit()
            self.monitor_digital_inputs_thread.wait()
        except Exception as e:
            print("Error al detener el hilo de monitoreo de entradas digitales")

   

        #Stop timer
        self.timer.stop()

        print("Enciendiendo pantalla LCD 100%")

        self.Rs485.send_command("FF00FFA50060100D04D05C016402B7")

        #putting back HMI in monitor mode
        self.Rs485.send_command("FF00FFA50060100D04D05101000248")

        #Flag to not add register if test are not performed
        self.dont_add_register=True

        self.btnPrueba3.setStyleSheet("background-color: red;")
        self.btnPrueba4.setStyleSheet("background-color: red;")
        self.btnPrueba5.setStyleSheet("background-color: red;")
        self.btnPrueba6.setStyleSheet("background-color: red;")

        self.btnResultados.setStyleSheet("background-color: red;")
        self.Test_6_signal.emit()

############## TEST2   #####################################

    def test_2(self):
        print("Segunda prueba")

        #Read register to verify HMI presence in Fixture

        print("Encendiendo bobina para alimentar 5V a hmi")

        try: 
            self.gateway.write_coil(0,True)
        except Exception as e:
            print(f"Ha ocurrido un error al encender la bobina 5v : {e}")

        #IMPORTANT DELAY TO LET THE HMI TURN ON AND INICIALIZE
        time.sleep(4)

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

        self.Rs485.send_command('FF00FFA50060100D04D05101010249')

        print("Turning off LCD screen")

        self.Rs485.send_command("FF00FFA50060100D04D05C01000253")
         
        
        print("Obtaining firmware version ")
        firmware_version=str(self.Rs485.send_command("FF00FFA50060100D03D05600024B"))

        
        print(f"Firmware response:{firmware_version}")

        if firmware_version == '' or firmware_version=='None':
            self.lblVerifyFirmware.setText("Firmware NO capturado")
            self.lblVerifyFirmware.setStyleSheet("color: red;")

            #Test Button 
            self.btnPrueba2.setStyleSheet("background-color: red;")

             # Crear un QTimer para emitir la señal después de 3 segundos
            #QTimer.singleShot(6000, lambda: self.failed_firmware_version_signal.emit())

            # Crear un QTimer para emitir la señal después de 3 segundos
            QTimer.singleShot(6000, lambda: self.failed_firmware_version_signal.emit())

        else:
            self.txtFirmware.setText(firmware_version)

            self.lblVerifyFirmware.setText("Firmware capturado")
            self.lblVerifyFirmware.setStyleSheet("color: green;")
            #Test Button 
            self.btnPrueba2.setStyleSheet("background-color: green;")

            # Crear un QTimer para emitir la señal después de 3 segundos
            #QTimer.singleShot(5000, lambda: self.Test_2_signal.emit())

            self.test.result_T2(firmware_version)

            #Proceed with test 3
            #self.test_3()
            #Test Button 
            self.btnPrueba2.setStyleSheet("background-color: green;")

            # Crear un QTimer para emitir la señal después de 3 segundos
            QTimer.singleShot(3000, lambda: self.Test_2_signal.emit())

            

            #Proceed with test 3
            self.test_3()

    def failed_palm_button_signal(self):

        self.lblRequestHMI.setText("Botones NO detectados, prueba no iniciada")
        self.lblRequestHMI.setStyleSheet("color: red;")

        QTimer.singleShot(3000, lambda: self.test_2_failed_firmware_version_response())

    def detected_palm_button(self):

        self.lblRequestHMI.setText("Botones Detectado")
        self.lblRequestHMI.setStyleSheet("color: Green;")

        self.inicialize_thread.stop_monithoring_palm_button_thread()
        self.inicialize_thread.quit()
        self.inicialize_thread.wait()

        QTimer.singleShot(3000, lambda: self.Test_1_signal.emit())

        


        
  
    def test_2_failed_firmware_version_response(self):

        print("Apagando bobina para alimentar 5V a hmi")

        try: 
            self.gateway.write_coil(0,False)
        except Exception as e:
            print(f"Ha ocurrido un error al apagar la bobina 5v : {e}")


        self.btnPrueba1.setEnabled(True)
        self.btnPrueba1.setStyleSheet("background-color: rgb(36, 146, 255);")

        self.btnPrueba2.setStyleSheet("")

        #STOP timer
        self.timer.stop()
        self.lbltimer.setText(self.formatted_timer_time)

        #STOP monitoring HMI position thread
        #self.monitor_thread.stop_monithoring_HMI_thread()

        self.txtSerialCode.setText("")
        self.txtSerialCode.setEnabled(True)
        self.txtSerialCode.setFocus()

        self.txtQrcode.setText("")
        self.txtQrcode.setEnabled(True)

        self.lblVerifySerialCode.setText("")

        self.lblRequestHMI.setText("")

        self.txtFirmware.setText("")

        self.lblVerifyFirmware.setText("")

        #Restore log out button 
        self.btnLogout.setEnabled(True)
        self.btnTrazabilidad.setEnabled(True)

        #self.txtComunicacion232.setText("")

        #self.lblVerify232communication.setText("")

        

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


############## TEST3   #####################################
    def test_3(self):
        # Crear el hilo de prueba
        self.test3_thread = Test3Thread(self.Rs485, self.Camera, self.led_program)

        # Conectar señales para actualizar la interfaz
        self.test3_thread.update_led_signal.connect(self.update_leds)
        self.test3_thread.test_finished_signal.connect(self.process_test_3_verification)

        # Iniciar el hilo
        self.test3_thread.start()

    def update_leds(self, leds_results):
        led_names = [f"lblLED{i}" for i in range(1, 12)]
        led_input_names = [f"lblLEDInput{i}" for i in range(1, 12)]

        for i in range(1, 12):
            if i in leds_results and leds_results[i] == 1:
                getattr(self, led_names[i - 1]).setEnabled(True)
                getattr(self, led_input_names[i - 1]).setEnabled(False)

    def process_test_3_verification(self, result,leds_results):
        self.btnPrueba3.setStyleSheet("background-color: green;" if result == "PASS" else "background-color: red;")
        
        Test_3_result=f"{result,leds_results}"
        self.test.result_T3(Test_3_result)
        # Esperar 5 segundos antes de continuar con la siguiente prueba
        QTimer.singleShot(5000, lambda: self.Test_3_signal.emit())

        self.test3_thread.quit()
        self.test3_thread.wait()
         
        self.test_4()

    def Test_3_GUI_changes(self):

        self.stackedWidget.setCurrentIndex(8) 
    

  


############## TEST4   #####################################

    def test_4(self):
        # Crear el hilo de prueba
        self.test4_thread = Test4Thread(self.Rs485, self.Camera, self.ocr_program)

        # Conectar señales para actualizar la interfaz
        self.test4_thread.update_lcd_signal.connect(self.update_lcds)
        self.test4_thread.test_finished_signal.connect(self.process_test_4_verification)

        # Iniciar el hilo
        self.test4_thread.start()

    def update_lcds(self, lcds_results):
        lcd_names = [f"lblLCD{i}" for i in range(1, 12)]
        lcd_input_names = [f"lblLCDInput{i}" for i in range(0, 12)]

        for i in range(1, 12):
            if i in lcds_results and lcds_results[i] == 1:
                if hasattr(self, lcd_names[i - 1]):  # Verificar si el atributo existe
                    getattr(self, lcd_names[i - 1]).setEnabled(True)
                if hasattr(self, lcd_input_names[i - 1]):  # Verificar si el atributo existe
                    getattr(self, lcd_input_names[i - 1]).setEnabled(False)

    def process_test_4_verification(self, result,lcds_results):
        self.btnPrueba4.setStyleSheet("background-color: green;" if result == "PASS" else "background-color: red;")
        Test_4_result=f"{result,lcds_results}"
        self.test.result_T4(Test_4_result)
        # Esperar 5 segundos antes de continuar con la siguiente prueba
        QTimer.singleShot(5000, lambda: self.Test_4_signal.emit())
        self.test_5()



    def Test_4_GUI_changes(self):

        self.stackedWidget.setCurrentIndex(9) 


##############  TEST 5   ##########################
    def test_5(self):
        # Diccionario con el orden específico de los botones
        self.buttons_order = {
            "Display": '80', "Schedule 1": '01', "Schedule 2": '02',
            "Schedule 3": '04', "Quick Clean": '08', "Start/Stop": '10',
            "Up Arrow": '20', "Down Arrow": '40'
        }

        self.button_actuators_order={
            "1":2,"2":3,"3":4,"4":5,"5":6,"6":7,"7":8,"8":9
        }

        #activating actuator box 

        try: 
            self.gateway.write_coil(1,True)
        except Exception as e:
            print(f"Ha ocurrido un error al activar el piston de la caja de actuadores : {e}")

        time.sleep(2)

        print(self.buttons_order)

        
        # Crear un hilo para monitorear los botones
        self.monitor_buttons_thread = MonitorButtonsThread(self.buttons_order,self.button_actuators_order,self.Rs485,self.gateway)
        
        # Conectar las señales del hilo con los métodos de la clase principal
        self.monitor_buttons_thread.update_button_signal.connect(self.update_button_state)
        self.monitor_buttons_thread.test_finished_signal.connect(self.on_test_finished)

        # Iniciar el hilo
        self.monitor_buttons_thread.start()

    def update_button_state(self, button, button_input,status):
        # Actualizar la interfaz gráfica (esto debe ejecutarse en el hilo principal)
        print(f"Actualizando estado de los botones: {button}, {button_input}")
        if status==True:
            getattr(self, button).setEnabled(True)
            getattr(self, button_input).setEnabled(False)
        else:
            getattr(self, button).setEnabled(False)
            getattr(self, button_input).setEnabled(True)


    def on_test_finished(self,test_failed,buttons_results):
        # Lógica que se ejecuta cuando la prueba ha finalizado
        print("La prueba de botones ha finalizado.")

        #activating actuator box 

        try: 
            self.gateway.write_coil(1,False)
        except Exception as e:
            print(f"Ha ocurrido un error al desactivar el piston de la caja de actuadores : {e}")

        button_result_dict=buttons_results

        if test_failed==False:

            button_result="PASS"
            self.btnPrueba5.setStyleSheet("background-color: green;")
        else:
            button_result="FAIL"
            self.btnPrueba5.setStyleSheet("background-color: red;")


        self.test.result_T5(button_result,button_result_dict)

        # En lugar de time.sleep(6), usamos QTimer
        QTimer.singleShot(6000,self.Test_5_signal.emit)
        #QTimer.singleShot(6000,self.Test_5_signal.emit())
        #self.Test_5_signal.emit()
        self.test_6()  # Llamar a la siguiente prueba

    def Test_5_GUI_changes(self):

        self.stackedWidget.setCurrentIndex(10) 

    def cancel_test_button(self):            

        print("Cancelando prueba 5")

        reply = QMessageBox.question(
            self,
            'Cancelar prueba',
            '¿Estás seguro de que quieres cancelar la prueba',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            
            #Erase current session info
            #self.config.erase_user_and_shop_info()

            #Show again first screen app
            self.stackedWidget.setCurrentIndex(0)

            self.btnLogout.setEnabled(False)

            self.btnPrueba1.setEnabled(False)
            self.btnPrueba1.setStyleSheet("background-color: ;")

            #Disable inicialize button
            self.btnInicializar.setEnabled(True)
            self.btnConfiguracion.setEnabled(True)

            #Clear txtfields
            self.txtNumeroEmpleado.setText("")
            self.txtNumeroOrden.setText("")


            self.disconnect_all_devices()

            self.lblCurrentUser.setText("")
            self.lblCurrentOrder.setText("")


        else:
            pass


    ################ TEST 6   #######################
        

    def test_6(self):
        self.digital_order = {
             "Schedule 1": '01', "Schedule 2": '02',
            "Schedule 3": '04', "Quick Clean": '08'
        }

        self.digital_actuators_order={
            "1":10,"2":11,"3":12,"4":13
        }

        print(self.digital_order)
        
        # Crear un hilo para monitorear los botones
        self.monitor_digital_inputs_thread = MonitorDigitalEntrances(self.digital_order, self.digital_actuators_order,self.Rs485,self.gateway)
        
        # Conectar las señales del hilo con los métodos de la clase principal
        self.monitor_digital_inputs_thread.update_digital_input_signal.connect(self.update_button_state_digital)
        self.monitor_digital_inputs_thread.test_6_finished_signal.connect(self.on_test_6_finished)

        # Iniciar el hilo
        self.monitor_digital_inputs_thread.start()

    def update_button_state_digital(self, digital, digital_input):
        # Actualizar la interfaz gráfica (esto debe ejecutarse en el hilo principal)
        print(f"Actualizando estado de los botones: {digital}, {digital_input}")

        getattr(self, digital).setEnabled(True)
        getattr(self, digital_input).setEnabled(False)

    def on_test_6_finished(self):
        # Lógica que se ejecuta cuando la prueba ha finalizado
        #End digital entrances thread
        self.monitor_digital_inputs_thread.stop()

        self.monitor_digital_inputs_thread.quit()
        self.monitor_digital_inputs_thread.wait()

        print("La prueba de entradas digitales ha finalizado.")

        digital_result="PASS"

        self.btnPrueba6.setStyleSheet("background-color: green;")

        self.test.result_T6(digital_result)

         # En lugar de time.sleep(6), usamos QTimer
        QTimer.singleShot(6000,self.Test_6_signal.emit)
        #QTimer.singleShot(6000,self.Test_6_signal.emit())

        #Stop timer
        self.timer.stop()

        
 
    # Método para actualizar la interfaz de usuario de manera segura desde el hilo
    def update_digital_state(self, digital,digital_input):
        
        getattr(self, digital).setEnabled(True)
        getattr(self, digital_input).setEnabled(False)

    
    def Test_6_GUI_changes(self):

        self.stackedWidget.setCurrentIndex(11) 

        #Stop monitoring Hmi position thread
        #self.monitor_thread.stop()

        print("Apagando bobina para alimentar 5V a hmi")

        try: 
            self.gateway.write_coil(0,False)
        except Exception as e:
            print(f"Ha ocurrido un error al apagar la bobina 5v : {e}")
   
        self.show_resume()
    ################ RESUME ########################################

    def show_resume(self):

        print("Resumen de prueba")

        self.btnResultados.setStyleSheet("background-color: green;")

        Result1=self.test.test1_result
        self.lblResumenCodigoSerial.setText(Result1)

        Result2=self.test.test2_result
        self.lblResumenFirmware.setText(Result2)

        Result3=self.test.test3_result
        self.lblResumenLEDS.setText(Result3)

        Result4=self.test.test4_result
        self.lblResumenLCD.setText(Result4)

        Result5=self.test.test5_result
        self.lblResumenBotones.setText(Result5)

        Result6=self.test.test6_result
        self.lblResumeDigitalInputs.setText(Result6)

        if not self.dont_add_register:

            #Add register to GUI table and csv file
            self.add_register(Result1,Result2,Result3,Result4,Result5,Result6)

        # En lugar de time.sleep(6), usamos QTimer
        QTimer.singleShot(10000,self.Test_resume_signal.emit)
        #QTimer.singleShot(6000,self.Test_resume_signal.emit())

        #self.Test_resume_signal.emit()

    def Test_resume_GUI_changes(self):

        print("Reiniciar parametros de prueba")

        #Reset register
        self.test.clear_record()

        #Test_1
        self.txtSerialCode.setText("")
        self.txtSerialCode.setFocus()
        self.lblVerifySerialCode.setText("")
        self.txtSerialCode.setEnabled(True)
        self.btnPrueba1.setStyleSheet("background-color: ;")
        self.txtQrcode.setText("")
        self.txtQrcode.setEnabled(True)

        self.lblRequestHMI.setText("")

        self.lblRequestHMI.setStyleSheet("")

        #Test 2
        self.txtFirmware.setText("")
        self.lblVerifyFirmware.setText("")
        #self.txtComunicacion232.setText("")
        #self.lblVerify232communication.setText("")
        self.btnPrueba2.setStyleSheet("background-color: ;")

        
        #Test 3
        led_names = [f"lblLED{i}" for i in range(1, 12)]
        led_input_names = [f"lblLEDInput{i}" for i in range(1, 12)]

        for i in range (0, 11):
            getattr(self, led_names[i]).setEnabled(False)
            getattr(self, led_input_names[i]).setEnabled(True)
        
        self.btnPrueba3.setStyleSheet("background-color: ;")
        
        #Test 4

        lcd_names = [f"lblLCD{i}" for i in range(1, 11)]
        lcd_input_names = [f"lblLCDInput{i}" for i in range(1, 11)]
        #print(lcd_names)
        #print(lcd_input_names)

        for i in range(1,10):
           
            getattr(self, lcd_names[i]).setEnabled(False)
            getattr(self, lcd_input_names[i]).setEnabled(True)

        self.btnPrueba4.setStyleSheet("background-color: ;")

        #Test 5
        button_names = [f"lblButton{i}" for i in range(1, 9)]
        button_input_names = [f"lblButtonInput{i}" for i in range(1,9)]

        for i in range(0,8):
            
            getattr(self, button_names[i]).setEnabled(False)
            getattr(self, button_input_names[i]).setEnabled(True)
        
        self.btnPrueba5.setStyleSheet("background-color: ;")

        #Test 6
        digital_names = [f"lblDigital{i}" for i in range(1, 5)]
        digital_input_names = [f"lblDigitalInput{i}" for i in range(1,5)]

        for i in range(0,3):
            
            getattr(self, digital_names[i]).setEnabled(False)
            getattr(self, digital_input_names[i]).setEnabled(True)

        self.btnPrueba6.setStyleSheet("background-color: ;")

        #Resume

        self.lblResumenCodigoSerial.setText("")

        self.lblResumenFirmware.setText("")

        self.lblResumenLEDS.setText("")

        self.lblResumenLCD.setText("")

        self.lblResumenBotones.setText("")

        self.lblResumeDigitalInputs.setText("")

        self.btnResultados.setStyleSheet("background-color: ;")
    
        #Go back to main Screen test
        self.stackedWidget.setCurrentIndex(6) 

        self.btnPrueba1.setEnabled(True)
        self.btnPrueba1.setStyleSheet("background-color: rgb(36, 146, 255);")

        #Enable app functionality
        self.btnLogout.setEnabled(True)
        self.btnTrazabilidad.setEnabled(True)

        self.txtSerialCode.setFocus()

        #Rest Timer
        self.lbltimer.setText(self.formatted_timer_time)

        #Retrieve add register flag
        self.dont_add_register=False

      
    ###############   Traceability ########################################○
    def traceability(self):
        print("Abriendo trazabilidad")
        self.stackedWidget.setCurrentIndex(14)


    def add_register(self, Codigo,Firmware,LEDS_result,LCDS_result,Buttons_result,Entradas_result):

        #Get current user and shop order
        session_info = self.config.get_current_user()

        user=session_info[0]
        shop_order=session_info[1]

               
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%H:%M:%S_%d-%m-%y")
        Current_date = str(formatted_datetime)



        formatted_time = current_datetime.strftime("%H:%M:%S")
        Current_time=str(formatted_time)
       
        # Assembling the register
        # Table register
        register = {"Codigos":Codigo,"Firmware": Firmware,"LEDS": LEDS_result,"LCDS": LCDS_result,"Botones":Buttons_result, "Entradas": Entradas_result, "Fecha": Current_date}
      
        # Logic to verify number of table registers and only show 9 registers 
        table_registers = self.ResultsTable.rowCount()
        if table_registers > 17:
            self.ResultsTable.removeRow(17)
  
        # Register insertion at top of table
        row = 0  # Insert the new register at the top of the table
        row_count = self.ResultsTable.rowCount()  # Obtener el número de filas actual en la tabla
        self.ResultsTable.insertRow(row)  # Insertar una nueva fila en la tabla

        col = 0  # Columna inicial para insertar valores

        for key, value in register.items():
            item = QtWidgets.QTableWidgetItem(str(value))  # Crear un QTableWidgetItem con el valor del diccionario
            item.setTextAlignment(Qt.AlignCenter)  # Centrar el texto en la celda
            self.ResultsTable.setItem(row, col, item)  # Establecer el QTableWidgetItem en la celda correspondiente
            col += 1  # Mover a la siguiente columna para el próximo valor del diccionario
       
        csv_register = {"Numero Empleado":user,"Numero Orden":shop_order,"Codigos serial ,QR":Codigo,"Version Firmware": Firmware,"Prueba LEDS": LEDS_result,"Prueba LCDS": LCDS_result, "Prueba pulsacion Botones":Buttons_result,"Prueba entradas digitales": Entradas_result, "Hora y Fecha": Current_date}
        
        # Call csv register add function 
        self.test.add_csv_register(csv_register,user,shop_order)



if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()

    app.exec_()