import csv
import os
import json 
import shutil

import configparser

import datetime

from datetime import datetime, timedelta

class Manage_data():
    def __init__(self,):
        self.create_monthly_results_folder()

####################### FOLDER FUNCTIONS ######################################
    def create_results_folder(self):
        folder_path = "C:\\"
        folder_name = "MMI"  # Nombre de la carpeta que contendrá los resultados
        full_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path
    
    def create_monthly_results_folder(self):
        folder_path = "C:\\Registros MMI Prensa"

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
    
    def create_order_results_folder(self,job):
        folder_path = self.create_monthly_results_folder()
        folder_name = f"{job}"  # Nombre de la carpeta que contendrá los resultados
        full_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path
    
    def add_csv_register(self, register:dict):


         # Obtener fecha y hora actual
        current_datetime = datetime.now()

        # --- Ajustar "día operativo" a partir de las 7:00 a.m. ---
        if current_datetime.hour < 7:
            # Si aún no son las 7:00 a.m., usar la fecha del día anterior
            operational_date = current_datetime - timedelta(days=1)
        else:
            operational_date = current_datetime


        formatted_datetime = operational_date.strftime("%d-%m-%Y")
        Current_date = str(formatted_datetime)
        print(f"Archivo operativo del día: {Current_date}")

        # Crear la carpeta para los archivos CSV
        folder_path = self.create_monthly_results_folder()
        #Csv_filename = os.path.join(folder_path, f"{part_number}_{Current_date}.csv")  # Ruta del archivo CSV
        Csv_filename = os.path.join(folder_path, f"{Current_date}.csv")  # Ruta del archivo CSV

        # Abrir el archivo CSV con codificación UTF-8
        with open(Csv_filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=register.keys())
            
            # Verificar si el archivo CSV ya existe o si es nuevo
            if file.tell() == 0:
                writer.writeheader()  # Si el archivo está vacío, escribirá los nombres de las columnas
            
            # Escribir el registro en el archivo CSV
            writer.writerow(register)

    ############  PIECE COUNTER FUNCTIONS ##########################################
    def obtain_piece_register_id_and_test(self):
        try:

            filepath= self.obtain_filepath()
            
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
                id_piezas_malas=ultima_fila.get('Piezas_malas', '0')  # Usar '0' como valor predeterminado

                # Convertir a enteros
                int_id_prueba = int(id_prueba) if id_prueba.isdigit() else 0
                int_id = int(id) if id.isdigit() else 0

                int_id_piezas_malas= int(id_piezas_malas) if id_piezas_malas.isdigit() else 0

                return  int_id_prueba,int_id,int_id_piezas_malas

        except FileNotFoundError:
            print(f"Error: El archivo {filepath} no existe.")
            return 0, 0,0
        except PermissionError:
            print(f"Error: No tienes permisos para leer el archivo {filepath}.")
            return 0, 0,0
        except Exception as e:
            print(f"Error inesperado al procesar el archivo {filepath}: {e}")
            return 0, 0,0

    def obtain_filepath(self):
        try:
            base_filepath = self.create_monthly_results_folder()

            current_datetime = datetime.now()
            # --- Ajuste del día operativo (7:00 a.m.) ---
            if current_datetime.hour < 7:
                operational_date = current_datetime - timedelta(days=1)
            else:
                operational_date = current_datetime

            formatted_datetime = operational_date.strftime("%d-%m-%Y")
            Current_date = str(formatted_datetime)

            # Construir el path base
            #fullpath = os.path.normpath(f"{base_filepath}\\{shop_order}")
            #fullpath = os.path.normpath(f"{base_filepath}\\{Current_date}")
            fullpath = os.path.normpath(f"{base_filepath}")

            if not os.path.exists(fullpath):
                os.makedirs(fullpath)

            # Nombre del archivo que debe existir: part_number.csv
            archivo_buscado = f"{Current_date}.csv"

            # Ruta completa al archivo
            ruta_archivo = os.path.join(fullpath, archivo_buscado)

            # Verificar si el archivo existe
            if os.path.isfile(ruta_archivo):
                # Aquí puedes avanzar en tu secuencia y trabajar con el archivo
                print(f"Archivo encontrado: {ruta_archivo}")
                return ruta_archivo
            else:
                # El archivo no existe
                print(f"Archivo '{archivo_buscado}' no encontrado en la carpeta '{fullpath}'")
                return None
        except Exception as e:
            print(f"Error inesperado al obtener la ruta del archivo: {e}")
            return None