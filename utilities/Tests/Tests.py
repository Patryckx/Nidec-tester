from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt

from PyQt5.QtCore import QTimer
import csv
import os
import json 

import datetime

from datetime import datetime




class Manage_tests():
    def __init__(self,):
        self.general_result=None
        self.test1_result=None
        self.test2_result=None
        self.test232_result=None
        self.test3_result=None
        self.test4_result=None
        self.test5_result=None
        self.test6_result=None
        self.record={}

        #Create results folder
        self.create_results_folder()
        #Create month results folder
        self.create_monthly_results_folder()


    def result (self,global_result:str):
        self.general_result=global_result

        self.record["Resutado general:"] = global_result

    def result_T1(self,serial_code:str,qrcode:str):
        self.test1_result=f"{serial_code} , {qrcode} "

        self.record["Prueba 1:"] = self.test1_result 

    def result_T2(self,firmware:str):
        self.test2_result=firmware
        self.record["Prueba 2:"] = firmware

    def result_232(self,response:str):
        self.test232_result=response
        self.record["Prueba 232:"] = response

    # def result_T3(self,leds_result:str,leds_array:list):
    #     self.test3_result=leds_result

    #     self.record["Prueba 3:"] = {
    #         "Resultado": leds_result,
    #         "Leds": leds_array
    #     }

    def result_T3(self,leds_result:str):
        self.test3_result=leds_result

        self.record["Prueba 3:"] = leds_result
        

    def result_T4(self,ocr_result:str):
        self.test4_result=ocr_result

        self.record["Prueba 4:"] = ocr_result

    def result_T5(self,result:str,buttons_result:str):

        self.test5_result=f"{result} , {buttons_result} ".replace('(', '').replace(')', '')


        self.record["Prueba 5:"] = self.test5_result

    def result_T6(self,result:str,digital_results:str):
        self.test6_result=f"{result} , {digital_results} ".replace('(', '').replace(')', '')


        self.record["Prueba 6:"] = self.test6_result
    
    def get_record(self):
        '''
        Obtain the results of the current test
        '''
        return self.record

    def clear_record(self):
        # Elimina todas las claves y valores del diccionario, dejándolo vacío
        self.record.clear()
####################### FOLDER FUNCTIONS ######################################
    def create_results_folder(self):
        folder_path = "C:\\"
        folder_name = "Registros Pentair HMI"  # Nombre de la carpeta que contendrá los resultados
        full_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path
    
    def create_monthly_results_folder(self):
        folder_path = "C:\\Registros Pentair HMI"

        '''current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d")'''
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%m-%Y")
        Current_date = str(formatted_datetime)
        folder_name = f"{Current_date}"  # Nombre de la carpeta que contendrá los resultados
        full_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path
    
    def create_order_results_folder(self,order):
        folder_path = self.create_monthly_results_folder()
        folder_name = f"{order}"  # Nombre de la carpeta que contendrá los resultados
        full_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path
    

    ######################## FILE TRACEABILITY FUNCTIONS ########################

    def add_csv_register(self, register,user,order):
        # Obtener la fecha y hora actual
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%d-%m-%Y")
        Current_date = str(formatted_datetime)
        print(Current_date)

        # Call folder create function for the csv files
        
        folder_path = self.create_order_results_folder(order) 
        Csv_filename = os.path.join(folder_path, f"{user}_{Current_date}.csv") # Created in traceability folder

        # Add register
        with open(Csv_filename, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=register.keys())
            # Verificar si el archivo CSV ya existe o si es nuevo
            if file.tell() == 0:
                writer.writeheader()  # Si el archivo está vacío, escribirá los nombres de las columnas
            writer.writerow(register)  # Write in the csv file
    
