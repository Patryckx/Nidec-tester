# PyQt5 Imports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QThread
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QMessageBox,
    QTableWidgetItem
)

# UI Import
from ui.Application import Ui_MainWindow as mainApplication

# Custom Libraries
from utilities.DAQ.DAQ import FX3U
from utilities.Telnet_lib.telnet import TelnetClient
from utilities.PySerial.PySerial_lib import SerialDevice
from utilities.Configuration.Config import Configuration
from utilities.Tests.Tests import Manage_tests
from utilities.Postgress_SQL.postgress_lib import PostgresDatabase
from utilities.Sqlite.sqlite_lib import SQLiteDatabase

from utilities.Logs.logger import setup_logger

setup_logger()

from datetime import datetime, timedelta
import configparser
import sys
import time
import os
import csv
import logging
import re
import time


#ERROR LOGS FUNCTION
def excepthook(exc_type, exc_value, exc_traceback):
    if logging.getLogger().hasHandlers():
        logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

    msg = QMessageBox()
    msg.setWindowTitle("Error en la aplicación")
    msg.setText("Ha ocurrido un error inesperado.")
    msg.setIcon(QMessageBox.Critical)
    msg.exec()

sys.excepthook = excepthook

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
        
        # Realizar el disparo y leer la respuesta
        self.Camera.send_data('T2')
        time.sleep(0.5)  # Esperar un breve momento
        results = self.Camera.read_data()
        print(f"resultadoss {results}")

        resultados_herramientas = self.procesar_respuesta(results)
        print(resultados_herramientas)

        # Determinar si la prueba pasó o falló
        test_3_results = "FAIL" if "NG"  in results or "ER" in results else "PASS"

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

        # Realizar el disparo y leer la respuesta
        self.Camera.send_data('T2')
        time.sleep(0.5)  # Esperar un breve momento
        results = self.Camera.read_data()

        resultados_herramientas = self.procesar_respuesta(results)
        print(resultados_herramientas)
        
        test_4_results = "FAIL" if "NG"  in results or "ER" in results else "PASS"
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
    test_finished_signal = pyqtSignal(bool,dict,bool,bool)

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
        config = configparser.ConfigParser()
        config.read('settings/settings.ini')
        actuator_sensor_value = config.get('Instruments', 'actuator_sensor', fallback='False').replace('"', '').lower() 

        if actuator_sensor_value=='true':
            actuator_sensor=True
        else:
            actuator_sensor=False


        fail_on_button_test = False
        attempts = 0

        #max_attempts = int(config.get('Instruments', 'actuator_sensor', fallback=6) )

        max_attempts = 6

        if actuator_sensor:
            actuator_sensor_required=True

            while attempts < max_attempts:
                actuator_in_position = self.gateway.read_coil(18)
                attempts += 1
                self.msleep(1000)  # Evita bloquear la GUI
                if actuator_in_position:
                    self.msleep(3000)
                    self.process_buttons(actuator_sensor_required,actuator_in_position)
                    return

            fail_on_button_test = True
            print("Actuador no detectado")

            self.test_finished_signal.emit(fail_on_button_test, self.button_results_dict,actuator_sensor_required,actuator_in_position)
        else:
            actuator_sensor_required=False
            self.process_buttons(actuator_sensor_required,actuator_sensor)

        

    def process_buttons(self,actuator_sensor_required,actuator_sensor):
        #Test flag
        fail_on_button_test=False
        
        while self.pending_buttons_list and self.pending_button_actuator_list and self.running:
            current_coil = self.pending_button_actuator_list.pop(0)
            print(f"Activando bobina {current_coil}")

            try:
                self.gateway.write_coil(current_coil, True)
            except Exception as e:
                print(f"Ocurrió un error al encender la bobina: {e}")

            attempts = 0
            max_attempts = 6
            detected = False


            while attempts < max_attempts and self.running:
                response = self.rs485.send_command("FF00FFA50060100D04D05101000248")
                print(response)
                hex_value = response[24:26]

                if hex_value == self.pending_buttons_list[0]:
                    print(f"Botón detectado: {hex_value}")
                    current_index = self.pending_buttons_index.pop(0)
                    button = f"lblButton{current_index}"
                    button_input = f"lblButtonInput{current_index}"
                    self.button_results_dict[current_index] = 1
                    self.update_button_signal.emit(button, button_input, True)
                    detected = True
                    break
                

                attempts += 1
                print(f"Intento {attempts} de {max_attempts} para detectar el botón.")

            print(f"Desactivando bobina {current_coil}")
            try:
                self.gateway.write_coil(current_coil, False)
            except Exception as e:
                print(f"Ocurrió un error al desactivar la bobina: {e}")

            if not detected:
                print("Botón no detectado tras 5 intentos.")
                current_index = self.pending_buttons_index.pop(0)
                button = f"lblButton{current_index}"
                button_input = f"lblButtonInput{current_index}"
                self.update_button_signal.emit(button, button_input, False)
                self.button_results_dict[current_index] = 0

                fail_on_button_test=True

            self.pending_buttons_list.pop(0)

        if not self.pending_buttons_list:
            print("Todos los botones han sido procesados.")

            self.test_finished_signal.emit(fail_on_button_test, self.button_results_dict,actuator_sensor_required,actuator_sensor)
            #self.test_finished_signal.emit(fail_on_button_test, self.button_results_dict)
            #self.test_finished_signal.emit(False, self.button_results_dict)


    def stop(self):
        self.running = False

class MonitorDigitalEntrances(QThread):
    # Definir señales para la comunicación con el hilo principal
    digital_input_detected_signal = pyqtSignal(str)
    update_digital_input_signal = pyqtSignal(str, str,bool)
    test_6_finished_signal = pyqtSignal(bool,dict)

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

        # Inicializar el diccionario con claves de 1 a n, con valores en None
        self.digital_entrances_results_dict = {i + 1: None for i in range(len(self.pending_digital_list))}
        print(self.digital_entrances_results_dict)
        #Clear results dictionary button
        self.digital_entrances_results_dict.clear()

    def run(self):
        #Flag to check if the test failed
        fail_on_digital_test=False
        while self.pending_digital_list and self.pending_actuator_list and self.digital_entrances_thread_isrunning:
            current_coil = self.pending_actuator_list[0]  # Obtener la bobina actual
            print(f"Activando bobina {current_coil}")
            try:
                self.gateway.write_coil(current_coil, True)  # Encender bobina
            except Exception as e:
                print(f"Ocurrio un error al encender la bobina: {e}")
                
            attempts = 0  # Contador de intentos
            max_attempts = 5

            detected = False
            
            while attempts < max_attempts and self.digital_entrances_thread_isrunning:
                response = self.rs485.send_command("FF00FFA50060100D04D05101000248")  # Obtener respuesta
                print(response)
                hex_value = response[26:28]  # Extrae el valor hexadecimal relevante
                
                if hex_value == self.pending_digital_list[0]:
                    print(f"Entrada detectada: {hex_value}")
                    current_index = self.pending_digital_index.pop(0)
                    print(current_index)
                    digital = f"lblDigital{current_index}"
                    digital_input = f"lblDigitalInput{current_index}"

                    #Guardar resultado en el diccionario
                    self.digital_entrances_results_dict[current_index] = 1

                    # Emitir una señal para actualizar la GUI en el hilo principal
                    self.update_digital_input_signal.emit(digital, digital_input,True)

                    detected = True
                    break
                
                attempts += 1
                print(f"Intento {attempts} de {max_attempts} para detectar la entrada")
            
            print(f"Desactivando bobina {current_coil}")
            try:
                self.gateway.write_coil(current_coil, False)  # Apagar bobina
            except Exception as e:
                print(f"Ocurrio un error al desactivar la bobina: {e}")

            # if attempts >= max_attempts:
            #     print(f"Entrada no detectada después de {max_attempts} intentos.")
            
            if not detected:
                print(" Entrada NO detectada tras 5 intentos.")
                current_index = self.pending_digital_index.pop(0)
                button = f"lblButton{current_index}"
                button_input = f"lblButtonInput{current_index}"
                self.update_digital_input_signal.emit(button, button_input,False)

                #Guardar resultado en el diccionario
                self.digital_entrances_results_dict[current_index] = 0

                fail_on_digital_test=True


            # Eliminar elementos procesados
            self.pending_digital_list.pop(0)
            self.pending_actuator_list.pop(0)

            if not self.pending_digital_list:
                print("Todas las señales han sido capturadas.")
                self.test_6_finished_signal.emit(fail_on_digital_test,self.digital_entrances_results_dict)  # Emitir señal para indicar que la prueba ha finalizado
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
        
        #Instance config class
        self.config=Configuration()

        self.gateway=FX3U()

        self.test=Manage_tests()

        #self.postgress_database=PostgresDatabase() 

        self.sqlite_database=SQLiteDatabase()



        # Space bar function initialized flag 
        self.initialized_flag = False
        #Flag to not add register if timer goes up
        self.dont_add_register=None
        
        #Serial Code scanned flag
        self.serial_code_captured=None

        self.is_database_enabled=self._read_database_activation_flag()


        #Timer test 
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)  # Conectar la señal timeout a la función
        self.remaining_time = 0  # Variable para almacenar el tiempo restante

        #Traceability table
        self.setup_table()

        # Lista para almacenar los hilos activos
        self.threads = []
        
        #Disable stop button 
        self.btnLogout.setEnabled(False)

        #Counters
        self.piece_id=None
        self.test_id=None
        self.bad_piece_id=None


        # Asegurar que la ventana pueda recibir eventos de teclado
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()



    ############# TABLE FUNCTIONS   ########################## 


    def setup_table(self):

        try:
            # Formato a tabla
            headers = ['Codigo','Firmware','Comunicación232','LED', 'LCDS','Botones','Entradas','Fecha' ]
            # Configuración de la tabla
            self.ResultsTable.setColumnCount(len(headers))
            self.ResultsTable.setHorizontalHeaderLabels(headers)

            # Ajustar el ancho de las columnas
            self.ResultsTable.setColumnWidth(headers.index('Codigo'), 120)
            self.ResultsTable.setColumnWidth(headers.index('Firmware'), 120)
            self.ResultsTable.setColumnWidth(headers.index('Comunicación232'), 150)
            self.ResultsTable.setColumnWidth(headers.index('LED'), 120)
            self.ResultsTable.setColumnWidth(headers.index('LCDS'), 120)
            self.ResultsTable.setColumnWidth(headers.index('Botones'), 120)
            self.ResultsTable.setColumnWidth(headers.index('Entradas'), 120)
            self.ResultsTable.setColumnWidth(headers.index('Fecha'), 200)

            # Actualizar la vista
            self.ResultsTable.update()

            # Cargar los últimos registros según la orden y usuario actual
            session_info = self.config.get_current_user()
            numero_orden = session_info[1]
            numero_empleado = session_info[0]

            self.load_traceability_from_db_to_table(
                conditions={"numero-orden": numero_orden, "numero-empleado": numero_empleado},
                limit=22
            )


        except Exception as e:
            print("Error seting up tracaebility table: ",e)
 
    
    def load_traceability_from_db_to_table(self, conditions: dict = None, limit: int = 22):
        """
        Carga los registros obtenidos desde la base de datos y los muestra en la tabla PyQt5.
        """
        try:
            # Obtener los datos desde la base de datos
            registros = self.sqlite_database.get_records_with_conditions(
                table_name="pentair-tester-registers",
                conditions=conditions,
                limit=limit
            )

            # Definir encabezados
            headers = ['Codigo', 'Firmware', 'Comunicación232', 'LED', 'LCDS', 'Botones', 'Entradas', 'Fecha']
            self.ResultsTable.setColumnCount(len(headers))
            self.ResultsTable.setHorizontalHeaderLabels(headers)

            # Limpiar tabla
            self.ResultsTable.setRowCount(0)

            # Llenar la tabla
            for row_index, registro in enumerate(registros):
                self.ResultsTable.insertRow(row_index)
                for col_index, key in enumerate(headers):
                    value = registro.get(key, "")
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.ResultsTable.setItem(row_index, col_index, item)

            print(f"Se cargaron {len(registros)} registros en la tabla.")

        except Exception as e:
            print(f"Error al mostrar registros en la tabla: {e}")
        
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

        try:
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

        except Exception as e:
            print("Error executing timer out function: ",e)
        

    def stop_all_threads(self):
        try:
            """Detiene todos los hilos activos."""
            print("Stopping all threads...")
            for thread in self.threads:
                if thread.is_alive():
                    # Aquí podrías implementar una señal o flag para detener hilos seguros
                    print(f"Stopping thread {thread.name}")
            self.threads.clear()  # Limpia la lista de hilos

        except Exception as e:
            print("Error exeuting stop all thread function:",e)
            raise

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

        

        #Test 1 timer 

        self.Test_1_signal.connect(self.test_2)

        #Firmware version Test 2
        self.Test_2_signal.connect(self.Test_2_GUI_changes)
        self.failed_firmware_version_signal.connect(self.test_2_failed_firmware_version_response)


        #LEDs test 3
        self.Test_3_signal.connect(self.Test_3_GUI_changes)

        #LCD Test 4
        self.Test_4_signal.connect(self.Test_4_GUI_changes)

        #Test 5 
        self.Test_5_signal.connect(self.Test_5_GUI_changes)


        #Test 6
        self.Test_6_signal.connect(self.Test_6_GUI_changes)

        #Resume test

        self.Test_resume_signal.connect(self.Test_resume_GUI_changes)



    
################## CONFIGURATION #############################################
    def show_edit_screen_configuration(self,event):
        try:
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

        except Exception as e:
            print("Error showing edit screen config:",e)
    

    def show_configuration(self,event):
        try:
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
        except Exception as e:
            print("Error showing configuration:",e)
        
    def save_configuration(self, event):

        try:
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

        except Exception as e:
            print("Error saving current configuration:",e)
            raise
    
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
        try:
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
        except Exception as e:
            print("Error verifying user and order:",e)
            raise

    
    def confirm_and_save_userId_and_ShopOrder(self,event):
        try:

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

        except Exception as e:
            print("Error saving and confirm user and order:",e)
            raise

    
    def deny_userId_and_ShopOrder(self,event):

        try:

            #Erase information in textfields
            self.txtNumeroEmpleado.setText("")
            self.txtNumeroOrden.setText("")
            
            #Show again user input information 
            self.stackedWidget.setCurrentIndex(4)

        except Exception as e:
            print("Error canceling user and order input:",e)
            raise

    def log_out(self):  

        try:          

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

                self.lblPiezasBuenas.setText("")
                self.lblPiezasMalas.setText("")
                #Restore inicialized app flag
                self.initialized_flag=False

                self.piece_id=0
                self.test_id=0
                self.bad_piece_id=0


            else:
                pass

        except Exception as e:
            print("Error in log out function:",e)
            raise

    def disconnect_all_devices(self):
        try:
            self.gateway.close()
            #self.Rs232.disconnect()
            self.Rs485.disconnect()
            self.Camera.close_connection()
        except Exception as e:
            print("Error disconnecting all devices...",e)

            



    ################ INICIALIZE  #################################

    def back_to_inicialize_app(self):
        self.stackedWidget.setCurrentIndex(0)

    def inicialize(self,event):

        try:
            print("App inicialized")

            print("Obtaining instruments configuration")
            current_config=self.config.get_current_config()

            gateway_port=current_config[0]
            RS232_port=current_config[1]
            RS485_port=current_config[2]
            camera_address=current_config[3]
            camera_port=current_config[4]
            self.timer_value = int(current_config[5])  
            self.led_program=current_config[6]
            self.ocr_program=current_config[7]


            # Convertir segundos a minutos y segundos
            minutes, seconds = divmod(  self.timer_value, 60)
            self.formatted_timer_time = f"{minutes:02}:{seconds:02}"  # Formato MM:SS

            self.lbltimer.setText(self.formatted_timer_time)

            print("Verifiying instruments...")

            print("Verifiying Serial port ")
            try:
                self.gateway.open(gateway_port)
            except Exception as e:
                print(f"Error de conexion 485: {e}")

            if not self.gateway.is_connected():
                self.stackedWidget.setCurrentIndex(2)
                return

            #Housekeeping registers gateway
            try:
                self.housekeeping_gateway()
            except Exception as e :
                print(f"Error: {e}" )

            try:
                self.Rs485 = SerialDevice(port=RS485_port, baudrate=9600, timeout=1)
            except Exception as e:
                print(f"Error de conexion 485: {e}")
            if not self.Rs485.connect():
                print("Serial 485 Device NOT connected connected")
                self.stackedWidget.setCurrentIndex(1)
                return

            #Camera Connection through telnet protocol

            try:
            
                self.Camera=TelnetClient(camera_address,camera_port)
            except Exception as e:
                print(f"Error al conectar con la camara{e}")

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

                currentUserId=str(data[0])
                self.lblCurrentUser.setText(currentUserId)

                currentShopOrder=str(data[1])
                self.lblCurrentOrder.setText(currentShopOrder)

                

                if self.is_database_enabled:

                    self.verify_data_sqlite(currentUserId,currentShopOrder)
                else:    
                    self.verify_data_csv()

                #"if is_data_valid:
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
        except Exception as e:
            print("Error incializing application:",e)


    def verify_data_csv(self):
        try:

            # Obtain file path
            filepath=self.obtain_filepath()

            if filepath:
                #Obtain id and id test
                self.piece_id,self.test_id,self.bad_piece_id=self.obtain_piece_register_id_and_test(filepath)
                print(f"Piezas OK{self.piece_id}")
                print(f"Piezas NG {self.bad_piece_id}")
                print(f"Contador pruebas{self.test_id}")

                self.lblPiezasBuenas.setText(str( self.piece_id))
                self.lblPiezasMalas.setText(str( self.bad_piece_id))

            else:
                self.piece_id=0
                self.test_id=0
                self.bad_piece_id=0
                self.lblPiezasBuenas.setText(str( self.piece_id))
                self.lblPiezasMalas.setText(str( self.bad_piece_id))



        except Exception as e:
            print(f"Error obtaining most recent path file to csv: {e}")


    def verify_data_sqlite(self, user,order):

        try:
            database_config=self.config.get_sqlite_database_information()

            database_path=database_config[0]
            database_table=database_config[1]
            #table_name=database_config[2]
            #Database connection
                
            self.sqlite_database.create_connection(database_path)

            # Parámetros para tu búsqueda
            table_name = 'nidec-pentair-tester'

            # Columnas que deseas obtener del registro
            desired_fields = ['id-prueba', 'id-pieza-ok','id-pieza-ng']

            conditions = {
            "numero-usuario": user,
            "numero-orden": order
                }
            # Obtener el registro más reciente desde PostgreSQL
            record = self.sqlite_database.get_last_record_fields_by_columns(
                table_name=database_table,
                conditions=conditions,
                fields=desired_fields
            )

            if record:
                # Extraer valores específicos del registro
                self.test_id = record.get('id-prueba', 0)
                self.piece_id = record.get('id-pieza-ok', 0)
                self.bad_piece_id=record.get('id-pieza-ng', 0)

                # Mostrar resultados en la interfaz
                print(f"Piezas OK DB: {self.piece_id}")
                print(f"Piezas NG DB: {self.bad_piece_id}")
                print(f"Contador pruebas DB: {self.test_id}")


                self.lblPiezasBuenas.setText(str(self.piece_id))
                self.lblPiezasMalas.setText(str(self.bad_piece_id))
                return True
            else:
                # Si no hay registro, reiniciar valores
                print("Orden no encontrada en base de datos")

                self.piece_id=0
                self.test_id=0
                self.bad_piece_id=0
                self.lblPiezasBuenas.setText(str( self.piece_id))
                self.lblPiezasMalas.setText(str(self.bad_piece_id))

                return False

        except Exception as e:
            print(f"Error al obtener datos desde SQlite: {e}")
            return None

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
            raise

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
            raise
        
           
        try: 
            self.gateway.write_coil(12,False)
            self.gateway.write_coil(13,False)
            self.gateway.write_coil(14,False)
            self.gateway.write_coil(15,False)



        except Exception as e:
            print(f"Ha ocurrido un error al activar el piston de la caja de actuadores : {e}")
            raise


       

    def test_inicialize(self):

        #Show first test screen
        self.stackedWidget.setCurrentIndex(6)

    def test1_verify_serial_code(self):

        try:
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


        except Exception as e:
            print("Error verifying serial codes:",e)    
            raise

    
    def test_1(self,event=None):

        try:
        
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

                #Palmswitch_inicialize_Thread
                self.lblRequestHMI.setStyleSheet("color: #00aaff;")

                # Crear el objeto del hilo
                self.inicialize_thread = Palmswitch_inicialize_Thread(self.gateway)
                self.inicialize_thread.inicialize_signal.connect(self.detected_palm_button)
                self.inicialize_thread.failed_inicialize_signal.connect(self.failed_palm_button_signal)
                self.inicialize_thread.stop_monitoring_palm_button_signal.connect(self.inicialize_thread.stop_monithoring_palm_button_thread)

                # Iniciar el hilo
                self.inicialize_thread.start()
                
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
        except Exception as e:
            print("Error on test 1:",e)
            raise

############## TEST2   #####################################

    def test_2(self):
        try:
            print("Segunda prueba")

            #Read register to verify HMI presence in Fixture

            print("Encendiendo bobina para alimentar 5V a hmi")

            try: 
                self.gateway.write_coil(0,True)
            except Exception as e:
                print(f"Ha ocurrido un error al encender la bobina 5v : {e}")

            #IMPORTANT DELAY TO LET THE HMI TURN ON AND INICIALIZE
            #time.sleep(3)

            #MORE DELAY TIME DUE BOOT DELAY PROBLEM IN HMIS
            time.sleep(5)

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


            #########################################################
            # print("Enabling command mode in HMI ")

            # self.Rs485.send_command('FF00FFA50060100D04D05101010249')

            command = 'FF00FFA50060100D04D05101010249'
            max_retries = 3
            delay = 1  # Tiempo de espera en segundos entre intentos

            for attempt in range(1, max_retries + 1):
                response = self.Rs485.send_command(command)

                if response:  # Si recibimos una respuesta válida, salir del bucle
                    print(f"Response received: {response}")
                    break

                print(f"Attempt {attempt}: No response received, retrying...")
                time.sleep(delay)  # Esperar antes de reintentar

            if not response:
                print("No response after maximum retries, continuing execution...")
            ############################################################
            

            print("Turning off LCD screen")

            self.Rs485.send_command("FF00FFA50060100D04D05C01000253")
            
            
            print("Obtaining firmware version ")
            firmware_version=str(self.Rs485.send_command("FF00FFA50060100D03D05600024B"))

            #Verify driver comunication though 232 
            driver_firmware_232_verification=self.verify_driver_comunication_232(firmware_version)

            print(f"Firmware response:{firmware_version}")

            if firmware_version == '' or firmware_version=='None':
                self.lblVerifyFirmware.setText("Firmware NO capturado")
                self.lblVerifyFirmware.setStyleSheet("color: red;")

                #Test Button 
                self.btnPrueba2.setStyleSheet("background-color: red;")

                # Crear un QTimer para emitir la señal después de 3 segundos
                #QTimer.singleShot(6000, lambda: self.failed_firmware_version_signal.emit())

                # def add_register(self, Codigo,Firmware,Comunicacion232,LEDS_result,LCDS_result,Buttons_result,Entradas_result):

                Result1=self.test.test1_result
                self.add_register(Result1,"FAIL","FAIL","FAIL","FAIL","FAIL","FAIL")

                

                # Crear un QTimer para emitir la señal después de 3 segundos
                QTimer.singleShot(5000, lambda: self.failed_firmware_version_signal.emit())

            elif not driver_firmware_232_verification:

                self.txtFirmware.setText(firmware_version)

                self.lblVerifyFirmware.setText("Firmware capturado & comunicación 232 verificada")
                self.lblVerifyFirmware.setStyleSheet("color: green;")
                #Test Button 
                self.btnPrueba2.setStyleSheet("background-color: green;")

                # Crear un QTimer para emitir la señal después de 3 segundos
                #QTimer.singleShot(5000, lambda: self.Test_2_signal.emit())

                self.test.result_T2(firmware_version)

                #Store 232 comunication verification result
                verificacion_232="PASS"

                self.test.result_232(verificacion_232)

                # Crear un QTimer para emitir la señal después de 3 segundos
                QTimer.singleShot(3000, lambda: self.Test_2_signal.emit())

                

                #Proceed with test 3
                self.test_3()


            else:
                self.txtFirmware.setText(firmware_version)

                self.lblVerifyFirmware.setText("Firmware capturado, comunicación 232 NO verificada")
                self.lblVerifyFirmware.setStyleSheet("color: orange;")
                #Test Button 
                self.btnPrueba2.setStyleSheet("background-color: orange;")

                # Crear un QTimer para emitir la señal después de 3 segundos
                #QTimer.singleShot(5000, lambda: self.Test_2_signal.emit())

                self.test.result_T2(firmware_version)

                #Store 232 comunication verification result
                verificacion_232="FAIL"

                self.test.result_232(verificacion_232)

                #Proceed with test 3
                #self.test_3()
                #Test Button 
                self.btnPrueba2.setStyleSheet("background-color: orange;")

                # Crear un QTimer para emitir la señal después de 3 segundos
                QTimer.singleShot(3000, lambda: self.Test_2_signal.emit())

                #Proceed with test 3
                self.test_3()
        except Exception as e:
            print("Error on test 2:",e)
            raise

    def verify_driver_comunication_232(self,cadena):

        try:
            """
            Verifica si todos los valores hexadecimales en el rango dado son '0'.
            
            :param cadena: La cadena hexadecimal completa.
            :param inicio: Índice de inicio de la parte relevante.
            :param fin: Índice de fin de la parte relevante.
            :return: True si todos los valores son '0', False en caso contrario.
            """
            inicio=44

            fin=80

            if inicio < 0 or fin > len(cadena):
                return False  # Evitar errores si los índices están fuera de rango
            
            parte_relevante = cadena[inicio:fin]  # Extraemos la parte a analizar
            
            # Verificamos si todos los caracteres en la parte relevante son '0'
            return all(c == '0' for c in parte_relevante)

        except Exception as e:
            print("Error on rs232 driver verification")
            

    def failed_palm_button_signal(self):
        try:

            self.lblRequestHMI.setText("Botones NO detectados, prueba NO iniciada")
            self.lblRequestHMI.setStyleSheet("color: red;")

            QTimer.singleShot(3000, lambda: self.test_2_failed_firmware_version_response())

        except Exception as e:
            print("Error performing failed palm button function :",e)
            raise

    def detected_palm_button(self):

        try:

            self.lblRequestHMI.setText("Botones detectados, iniciando prueba...")
            self.lblRequestHMI.setStyleSheet("color: Green;")

            self.inicialize_thread.stop_monithoring_palm_button_thread()
            self.inicialize_thread.quit()
            self.inicialize_thread.wait()

            QTimer.singleShot(2000, lambda: self.Test_1_signal.emit())

        except Exception as e:
            print("Error executing detected palm buttons function:",e)
            raise


        
  
    def test_2_failed_firmware_version_response(self):

        try:

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
        except Exception as e:
            print("Error executing test 2 failed firmware function: ",e)
            raise
        

    def Test_2_GUI_changes(self):
            #Third Test
            self.stackedWidget.setCurrentIndex(7)  



############## TEST3   #####################################
    def test_3(self):

        try:
            # Crear el hilo de prueba
            self.test3_thread = Test3Thread(self.Rs485, self.Camera, self.led_program)

            # Conectar señales para actualizar la interfaz
            self.test3_thread.update_led_signal.connect(self.update_leds)
            self.test3_thread.test_finished_signal.connect(self.process_test_3_verification)
            # Iniciar el hilo
            self.test3_thread.start()

        except Exception as e:
            print("Error executing test 3:",e)
            raise

    def update_leds(self, leds_results):
        try:
            led_names = [f"lblLED{i}" for i in range(1, 12)]
            led_input_names = [f"lblLEDInput{i}" for i in range(1, 12)]

            for i in range(1, 12):
                if i in leds_results and leds_results[i] == 1:
                    getattr(self, led_names[i - 1]).setEnabled(True)
                    getattr(self, led_input_names[i - 1]).setEnabled(False)
        except Exception as e:
            print("Error updating leds function:",e)
            raise
    def process_test_3_verification(self, result,leds_results):
        try:
            self.btnPrueba3.setStyleSheet("background-color: green;" if result == "PASS" else "background-color: red;")
            
            Test_3_result=f"{result,leds_results}"
            self.test.result_T3(Test_3_result)

            self.test3_thread.quit()
            self.test3_thread.wait()
            
            # Esperar 5 segundos antes de continuar con la siguiente prueba
            QTimer.singleShot(3000, lambda: self.Test_3_signal.emit())
            self.test_4()
        except Exception as e:
            print("Error processing test 3 verification function:",e)
            raise

    def Test_3_GUI_changes(self):

        self.stackedWidget.setCurrentIndex(8) 

############## TEST4   #####################################

    def test_4(self):

        try:
            # Crear el hilo de prueba
            self.test4_thread = Test4Thread(self.Rs485, self.Camera, self.ocr_program)

            # Conectar señales para actualizar la interfaz
            self.test4_thread.update_lcd_signal.connect(self.update_lcds)
            self.test4_thread.test_finished_signal.connect(self.process_test_4_verification)

            # Iniciar el hilo
            self.test4_thread.start()

        except Exception as e:
            print("Error on test 4:",e)
            raise

    def update_lcds(self, lcds_results):

        try:
            lcd_names = [f"lblLCD{i}" for i in range(1, 11)]
            lcd_input_names = [f"lblLCDInput{i}" for i in range(1, 11)]

            for i in range(1, 11):
                if i in lcds_results and lcds_results[i] == 1:
                    if hasattr(self, lcd_names[i - 1]):  # Verificar si el atributo existe
                        getattr(self, lcd_names[i - 1]).setEnabled(True)
                    if hasattr(self, lcd_input_names[i - 1]):  # Verificar si el atributo existe
                        getattr(self, lcd_input_names[i - 1]).setEnabled(False)
        except Exception as e:
            print("Error updating lcds:",e)
            raise


    def process_test_4_verification(self, result,lcds_results):

        try:
            self.btnPrueba4.setStyleSheet("background-color: green;" if result == "PASS" else "background-color: red;")
            Test_4_result=f"{result,lcds_results}"
            self.test.result_T4(Test_4_result)
            # Esperar 5 segundos antes de continuar con la siguiente prueba
            self.test4_thread.quit()
            self.test4_thread.wait()

            QTimer.singleShot(3000, lambda: self.Test_4_signal.emit())

            self.test_5()
        except Exception as e:
            print("Error processing test 4 verification: ",e)
            raise



    def Test_4_GUI_changes(self):

        self.stackedWidget.setCurrentIndex(9) 


##############  TEST 5   ##########################
    def test_5(self):

        try:
            # Diccionario con el orden específico de los botones
            # self.buttons_order = {
            #     "Display": '80', "Schedule 1": '01', "Schedule 2": '02',
            #     "Schedule 3": '04', "Quick Clean": '08', "Start/Stop": '10',
            #     "Up Arrow": '20', "Down Arrow": '40'
            # }

            # self.button_actuators_order={
            #     "1":2,"2":3,"3":4,"4":5,"5":6,"6":7,"7":8,"8":9
            # }
            self.buttons_order = {
                "Display": '80', "Schedule 1": '01', "Schedule 2": '02',
                "Schedule 3": '04', "Quick Clean": '08', "Start/Stop": '10',
                "Down Arrow": '40',"Up Arrow": '20'
            }

            self.button_actuators_order={
                "1":2,"2":3,"3":4,"4":5,"5":6,"6":7,"7":9,"8":8
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

        except Exception as e:
            print("Error on test 5: ",e)
            raise

    def update_button_state(self, button, button_input,status):

        try:
            # Actualizar la interfaz gráfica (esto debe ejecutarse en el hilo principal)
            print(f"Actualizando estado de los botones: {button}, {button_input}")
            if status==True:
                getattr(self, button).setEnabled(True)
                getattr(self, button_input).setEnabled(False)
            else:
                getattr(self, button).setEnabled(False)
                getattr(self, button_input).setEnabled(True)

        except Exception as e:
            print("Error updating buttons state :",e)
            


    def housekeeping_button_actuators(self):

        try:

            # 1. Apagar todos los actuadores pequeños primero
            print("Desactivando actuadores pequeños...")
            for coil in self.button_actuators_order.values():
                try:
                    self.gateway.write_coil(coil, False)
                except Exception as e:
                    print(f"Error al desactivar actuador {coil}: {e}")

            #activating actuator box 
            # Verificar que todos los actuadores pequeños realmente se apagaron
            for coil in self.button_actuators_order.values():
                try:
                    state = self.gateway.read_coil(coil)
                    if state:  # sigue en True
                        print(f"Actuador {coil} aún extendido, intentando forzar retracción...")
                        self.gateway.write_coil(coil, False)
                        time.sleep(0.3)  # pequeño retardo de seguridad
                except Exception as e:
                    print(f"Error al verificar estado de actuador {coil}: {e}")

            
            print("Esperando 2 segundos para garantizar retracción...")
            time.sleep(2)


            #QTimer.singleShot(2000, self.on_test_finished)
        except Exception as e:
            print("Error executing housekeeping buttons actuators function:",e)
            raise

        

    def on_test_finished(self,test_failed,buttons_results,actuator_sensor_required,actuator_sensor_result):

        try:
            # Lógica que se ejecuta cuando la prueba ha finalizado
            print("La prueba de botones ha finalizado.")

            self.housekeeping_button_actuators()
            try: 
                #self.msleep(1500) 
                self.gateway.write_coil(1,False)
            except Exception as e:
                print(f"Ha ocurrido un error al desactivar el piston de la caja de actuadores : {e}")

            if actuator_sensor_required:
                if not actuator_sensor_result:
                    self.lblButtonTestMsg.setText("Actuador NO detectado...")
                    self.lblButtonTestMsg.setStyleSheet("color: red;")
            

            button_result_dict=buttons_results

            if test_failed==False:

                button_result="PASS"
                self.btnPrueba5.setStyleSheet("background-color: green;")
            else:
                button_result="FAIL"
                self.btnPrueba5.setStyleSheet("background-color: red;")

            self.test.result_T5(button_result,button_result_dict)

            # En lugar de time.sleep(6), usamos QTimer
            QTimer.singleShot(4000,self.Test_5_signal.emit)
            #QTimer.singleShot(6000,self.Test_5_signal.emit())
            #self.Test_5_signal.emit()
            self.test_6()  # Llamar a la siguiente prueba
        except Exception as e:
            print("Error on test 5 finished function:",e)
            raise
    

    def Test_5_GUI_changes(self):

        self.stackedWidget.setCurrentIndex(10) 


    ################ TEST 6   #######################
        

    def test_6(self):

        try:
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
        except Exception as e:
            print("Error on test 6:",e)
            raise

    def update_button_state_digital(self, digital, digital_input,status):

        try:
            # Actualizar la interfaz gráfica (esto debe ejecutarse en el hilo principal)
            print(f"Actualizando estado de las entradas digitales: {digital}, {digital_input}")

            if status==True:
                getattr(self, digital).setEnabled(True)
                getattr(self, digital_input).setEnabled(False)
            else:
                getattr(self, digital).setEnabled(False)
                getattr(self, digital_input).setEnabled(True)

        except Exception as e:
            print(" Error updating buttons digital inputs signals:",e)

    def on_test_6_finished(self,test_failed,digital_entrances_results):

        try:
            # Lógica que se ejecuta cuando la prueba ha finalizado
            #End digital entrances thread
            self.monitor_digital_inputs_thread.stop()

            self.monitor_digital_inputs_thread.quit()
            self.monitor_digital_inputs_thread.wait()

            print("La prueba de entradas digitales ha finalizado.")

            digital_results_dict=digital_entrances_results

            if test_failed==False:
                digital_result="PASS"

                self.btnPrueba6.setStyleSheet("background-color: green;")

            else:
                digital_result="FAIL"

                self.btnPrueba6.setStyleSheet("background-color: red;")

            self.test.result_T6(digital_result,digital_results_dict)

            # En lugar de time.sleep(6), usamos QTimer
            QTimer.singleShot(4000,self.Test_6_signal.emit)
            #QTimer.singleShot(6000,self.Test_6_signal.emit())

            #Stop timer
            self.timer.stop()

        except Exception as e:
            print("Error on test 6 finished function: ",e)
            raise

        
 
    # Método para actualizar la interfaz de usuario de manera segura desde el hilo
    def update_digital_state(self, digital,digital_input):
        try:
            
            getattr(self, digital).setEnabled(True)
            getattr(self, digital_input).setEnabled(False)

        except Exception as e:
            print("Error updating digital state test 6 function: ",e)

    
    def Test_6_GUI_changes(self):

        try:

            self.stackedWidget.setCurrentIndex(11) 

            #Stop monitoring Hmi position thread
            #self.monitor_thread.stop()

            print("Apagando bobina para alimentar 5V a hmi")

            try: 
                self.gateway.write_coil(0,False)
            except Exception as e:
                print(f"Ha ocurrido un error al apagar la bobina 5v : {e}")
    
            self.show_resume()

        except Exception as e:
            print("Error on test 6 GUI Changes funtion:",e)
    ################ RESUME ########################################

    def show_resume(self):

        try:

        

            print("Resumen de prueba")

            self.btnResultados.setStyleSheet("background-color: green;")

            Result1=self.test.test1_result
            self.lblResumenCodigoSerial.setText(Result1)

            Result2=self.test.test2_result
            self.lblResumenFirmware.setText(Result2)

            Result232=self.test.test232_result

            Result3=self.test.test3_result
            self.lblResumenLEDS.setText(Result3)

            Result4=self.test.test4_result
            self.lblResumenLCD.setText(Result4)

            Result5=self.test.test5_result
            self.lblResumenBotones.setText(Result5)

            Result6=self.test.test6_result
            self.lblResumeDigitalInputs.setText(Result6)

            #Add test counter 
            self.test_id+=1

            #Verify if is a good piece

            if "PASS" in Result232 and "PASS" in Result3 and "PASS" in Result4 and "PASS" in Result5 and "PASS" in Result6:
                self.piece_id+=1

                self.lblPiezasBuenas.setText(str( self.piece_id))

            else:
                self.bad_piece_id+=1

                self.lblPiezasMalas.setText(str(self.bad_piece_id))


            if not self.dont_add_register:

                #Add register to GUI table and csv file
                self.add_register(Result1,Result2,Result232,Result3,Result4,Result5,Result6)

            # En lugar de time.sleep(6), usamos QTimer
            QTimer.singleShot(8000,self.Test_resume_signal.emit)
            #QTimer.singleShot(6000,self.Test_resume_signal.emit())

            #self.Test_resume_signal.emit()

        except Exception as e:
            print(" Error on show resume function: ",e)
            raise

    def Test_resume_GUI_changes(self):

        try:

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

            self.lblButtonTestMsg.setText("Verificando funcionalidad botones...")
            self.lblButtonTestMsg.setStyleSheet("color: ;")

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

            for i in range(0,10):
            
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
        except Exception as e:
            print("Error on show test resume Gui changes :",e)

      
    ###############   Traceability ########################################○
    def traceability(self):
        print("Abriendo trazabilidad")
        self.stackedWidget.setCurrentIndex(14)


    def add_register(self, Codigo,Firmware,Comunicacion232,LEDS_result,LCDS_result,Buttons_result,Entradas_result):

        try:

            #Get current user and shop order
            session_info = self.config.get_current_user()

            user=session_info[0]
            shop_order=session_info[1]

                
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%H:%M:%S_%d-%m-%y")
            Current_date = str(formatted_datetime)

            codigo_serial=str(self.serial_code)
            codigo_qr=str(self.qrcode)



            formatted_time = current_datetime.strftime("%H:%M:%S")
            Current_time=str(formatted_time)
        
            # Assembling the register
            # Table register
            register = {"Codigos":Codigo,"Firmware": Firmware,"Comunicación232":Comunicacion232,"LEDS": LEDS_result,"LCDS": LCDS_result,"Botones":Buttons_result, "Entradas": Entradas_result, "Fecha": Current_date}
        
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
        
            csv_register = {"ID_Prueba":self.test_id,"ID":self.piece_id,"ID_pieza_mala":self.bad_piece_id,"Numero Empleado":user,"Numero Orden":shop_order,"Codigos serial ,QR":Codigo,"Version Firmware": Firmware,"Comunicación232":Comunicacion232,"Prueba LEDS": LEDS_result,"Prueba LCDS": LCDS_result, "Prueba pulsacion Botones":Buttons_result,"Prueba entradas digitales": Entradas_result, "Hora y Fecha": Current_date}
            
            # Call csv register add function 
            self.test.add_csv_register(csv_register,user,shop_order)

            register_dict = {
                "id-prueba": self.test_id,
                "id-pieza": self.piece_id,
                "numero-empleado": user,
                "numero-orden": shop_order,
                "codigo-serial": codigo_serial,
                "codigo-qr":codigo_qr,
                "version-firmware": Firmware,
                "comunicacion-232": Comunicacion232,
                "prueba-leds": LEDS_result,
                "prueba-lcds": LCDS_result,
                "prueba-botones":Buttons_result,
                "prueba-entradas-digitales": Entradas_result,
                "id-pieza-mala":self.bad_piece_id
                
            } 
            try:

                database_config=self.config.get_sqlite_database_information()

                database_path=str(database_config[0])
                table=str(database_config[1])

                #Database connection
            
                self.sqlite_database.create_connection(database_path)

                #Insert register
                self.sqlite_database.insert_multiple_columns(table,register_dict)

                #Close connection 
                self.sqlite_database.close_connection()
            except Exception as e :
                print("Error al insertar registro en base de datos")   

        except Exception as e:
            print("Error on add register function: ",e)
            raise

############  TRACEABILITY  ##########################################
    def obtain_piece_register_id_and_test(self, filepath):
        try:
            with open(filepath, mode='r', newline='', encoding='utf-8') as archivo:
                # Leer el archivo CSV
                reader = csv.DictReader(archivo)
                
                # Leer todas las filas y almacenarlas en una lista
                filas = list(reader)
                
                # Verificar si hay filas en el archivo
                if not filas:
                    # Si no hay filas, devolver 0 en ambos casos
                    return 0, 0 ,0
                
                # Obtener la última fila
                ultima_fila = filas[-1]
                
                # Verificar si las columnas existen y devolver 0 si no existen
                id_prueba = ultima_fila.get('ID_Prueba', '0')  # Usar '0' como valor predeterminado
                id = ultima_fila.get('ID', '0')  # Usar '0' como valor predeterminado

                id_pieza_mala=ultima_fila.get('ID_pieza_mala', '0')

                # Convertir a enteros
                int_id_prueba = int(id_prueba) if id_prueba.isdigit() else 0
                int_id = int(id) if id.isdigit() else 0
                int_id_pieza_mala= int(id_pieza_mala) if id_pieza_mala.isdigit() else 0


                return  int_id,int_id_prueba,int_id_pieza_mala

        except FileNotFoundError:
            print(f"Error: El archivo {filepath} no existe.")
            return 0, 0 ,0
        except PermissionError:
            print(f"Error: No tienes permisos para leer el archivo {filepath}.")
            return 0, 0,0
        except Exception as e:
            print(f"Error inesperado al procesar el archivo {filepath}: {e}")
            return 0, 0,0

    def obtain_filepath(self):
        try:
            base_filepath = self.test.create_monthly_results_folder()

            # Obtener información del usuario y orden de tienda
            session_info = self.config.get_current_user()
            user = session_info[0]
            shop_order = session_info[1]

            # Construir el path base
            fullpath = os.path.normpath(f"{base_filepath}\\{shop_order}")

            if not os.path.exists(fullpath):
                os.makedirs(fullpath)

            # Obtener todos los archivos en el directorio
            archivos = os.listdir(fullpath)

            # Filtrar solo los archivos que siguen el formato user_fecha
            archivos_validos = [archivo for archivo in archivos if archivo.startswith(f"{user}_")]

            # Si no se encuentran archivos, retornar None o un valor adecuado
            if not archivos_validos:
                return None

            # Ordenar los archivos por fecha (formato: DD-MM-YYYY)
            archivos_validos.sort(key=lambda x: datetime.strptime(x.split('_')[1].split('.')[0], "%d-%m-%Y"), reverse=True)

            # El primer archivo de la lista será el de la fecha más reciente
            archivo_mas_reciente = archivos_validos[0]

            # Retornar el path completo del archivo más reciente
            return os.path.join(fullpath, archivo_mas_reciente)

        except Exception as e:
            print(f"Error inesperado al obtener la ruta del archivo: {e}")
            return None

    ########### .INI FLAGS  ################################### 

    def _read_database_activation_flag(self):
        config = configparser.ConfigParser()
        config.read('settings/settings.ini')
        response_setting = config.get('DATABASE', 'db_active', fallback="true").replace('"', '').strip().strip('"').lower()
        return response_setting == "true"



if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()

    app.exec_()