from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt

from PyQt5.QtCore import QTimer
import csv
import os
import json 

import datetime


class Manage_tests():
    def __init__(self,test1_result,test2_result,
                test3_result,test4_result,
                test5_result,test6_result):
        self.general_result=None
        self.test1_result=None
        self.test2_result=None
        self.test3_result=None
        self.test4_result=None
        self.test5_result=None
        self.test6_result=None
        self.record=[]

    def result (self,global_result:str):
        self.general_result=global_result

        self.record["Resutado general:"] = global_result

    def result_T1(self,serial_code:str):
        self.test1_result=serial_code

        self.record["Prueba 1:"] = serial_code

    def result_T2(self,firmware:str):
        self.test2_result=firmware
        self.record["Prueba 2:"] = firmware

    def result_T3(self,leds_result:str,leds_array:dict):
        self.test3_result=leds_result

        self.record["Prueba 3:"] = {
            "Resultado": leds_result,
            "Leds": leds_array
        }

    def result_T4(self,ocr_result:str):
        self.test4_result=ocr_result

        self.record["Prueba 4:"] = ocr_result

    def result_T5(self,buttons_result:str,buttons:dict):
        self.test5_result=buttons_result

        self.record["Prueba 5:"] = {
            "Resultado": buttons_result,
            "Botones": buttons
        }

    def result_T6(self,result:str,digital_inputs:dict):
        self.test6_result=result

        self.record["Prueba 6:"] = {
            "Resultado": result,
            "Entradas digitales": digital_inputs
        }
    
    def get_record(self):
        '''
        Obtain the results of the current test
        '''
        return self.record

    def clear_record(self):
        # Elimina todas las claves y valores del diccionario, dejándolo vacío
        self.record.clear()


    

    ######################## FILE TRACEABILITY FUNCTIONS ########################

    def csv_registers_add(self, register):
        # Csv registers file
        # Obtener la fecha y hora actual
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d")
        Current_date = str(formatted_datetime)
        print(Current_date)

        # Call folder create function for the csv files
        self.create_results_folder() 

        # Create folder for specific order
        folder_path = self.create_results_folder_archive() 

        # Csv_filename = (f"{Current_date}_registers.csv") # Csv file name created in current folder
        Csv_filename = os.path.join(folder_path, f"{Current_date}_registros.csv") # Created in traceability folder

        # Add register
        with open(Csv_filename, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=register.keys())
            # Verificar si el archivo CSV ya existe o si es nuevo
            if file.tell() == 0:
                writer.writeheader()  # Si el archivo está vacío, escribirá los nombres de las columnas
            writer.writerow(register)  # Write in the csv file
    
    def create_results_folder(self):
        folder_path = "C:\\Nidec"
        folder_name = "Registros Pentair Tester"  # Nombre de la carpeta que contendrá los resultados
        full_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path
    
    def create_results_folder_archive(self):
        folder_path = "C:\\Nidec\\Registros Etiqueta Z"

        '''current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d")'''
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m")
        Current_date = str(formatted_datetime)
        folder_name = f"{Current_date}"  # Nombre de la carpeta que contendrá los resultados
        full_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path