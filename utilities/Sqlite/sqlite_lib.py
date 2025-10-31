import sqlite3
from sqlite3 import Error

class SQLiteDatabase:
    def __init__(self):
        self.connection = None

    def create_connection(self, db_path):
        """Establece una conexión a la base de datos SQLite"""
        try:
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row  # permite obtener resultados como diccionarios
            print(f"Conexión exitosa a la base de datos SQLite: {db_path}")
            return self.connection
        except Error as e:
            print(f"Error al conectar a SQLite: {e}")
            return None

    def create_table(self, table_name):
        """Crea una tabla si no existe"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag_name TEXT NOT NULL,
                        value REAL,
                        fecha NUMERIC DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            print(f"Tabla '{table_name}' creada/verificada.")
        except Error as e:
            print(f"Error al crear tabla: {e}")

    def insert_data(self, table_name, tag, value):
        """Inserta datos en una tabla específica"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute(f"""
                    INSERT INTO {table_name} (tag_name, value)
                    VALUES (?, ?)
                """, (tag, value))
            print(f"Datos insertados en '{table_name}': Tag={tag}, Value={value}")
        except Error as e:
            print(f"Error al insertar datos: {e}")

    def insert_multiple_columns(self, table_name, data: dict):
        """Inserta datos en múltiples columnas"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return
        try:
            with self.connection:
                cursor = self.connection.cursor()
                safe_table_name = str(table_name).replace('"', '').replace("'", "")
                safe_columns = ', '.join([f'"{col}"' for col in data.keys()])
                placeholders = ', '.join(['?'] * len(data))
                values = tuple(data.values())
                sql = f'INSERT INTO "{safe_table_name}" ({safe_columns}) VALUES ({placeholders})'
                cursor.execute(sql, values)
            print(f"Datos insertados en '{table_name}': {data}")
        except Error as e:
            print(f"Error al insertar datos múltiples: {e}")

    def read_data(self, table_name):
        """Lee todos los registros de la tabla"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            records = cursor.fetchall()
            print(f"\nRegistros en '{table_name}':")
            for row in records:
                print(dict(row))
            return [dict(r) for r in records]
        except Error as e:
            print(f"Error al leer datos: {e}")
            return []

    def get_last_record(self, table_name):
        """Obtiene el último registro basado en la fecha más reciente"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT * FROM {table_name}
                ORDER BY fecha DESC
                LIMIT 1
            """)
            record = cursor.fetchone()
            print(f"Último registro en '{table_name}': {dict(record) if record else None}")
            return dict(record) if record else None
        except Error as e:
            print(f"Error al obtener el último registro: {e}")
            return None
        

    def get_last_record_fields_by_columns(self, table_name, conditions, fields):
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return None

        try:
            cursor = self.connection.cursor()

            # Asegurar nombres correctos
            safe_table_name = str(table_name).replace('"', '').replace("'", "")
            safe_columns = ', '.join([f'"{col}"' for col in fields])

            # Construir condiciones dinámicamente
            where_clauses = []
            values = []
            for col, val in conditions.items():
                where_clauses.append(f'"{col}" = ?')
                values.append(val)
            where_str = " AND ".join(where_clauses)

            # Query SQL segura
            sql = f"""
                SELECT {safe_columns}
                FROM "{safe_table_name}"
                WHERE {where_str}
                ORDER BY fecha DESC
                LIMIT 1
            """

            print("SQL ejecutado:", sql)
            print("Valores:", values)

            cursor.execute(sql, tuple(values))
            record = cursor.fetchone()

            if not record:
                print(f"No se encontró registro con {conditions}")
                return None

            # Convertir sqlite3.Row → dict
            record_dict = dict(record)

            print("Registro correcto:", record_dict)
            return record_dict

        except Exception as e:
            print(f"Error al obtener registro filtrado: {e}")
            return None
            


    def get_records_with_conditions(self, table_name, conditions: dict = None, limit: int = 22):
        """
        Obtiene una lista de registros desde la base de datos SQLite 
        aplicando condiciones opcionales y un límite de cantidad.
        
        Retorna: lista de diccionarios (cada registro es un dict con clave = nombre de columna)
        """
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return []

        try:
            cursor = self.connection.cursor()

            # Construcción dinámica de condiciones
            where_clauses = []
            values = []

            if conditions:
                for col, val in conditions.items():
                    where_clauses.append(f'"{col}" = ?')
                    values.append(val)
                where_str = " AND ".join(where_clauses)
            else:
                where_str = "1=1"

            # Límite
            limit_clause = f"LIMIT {limit}" if limit else ""

            table_name = str(table_name).replace('"', '').replace("'", "")
            # Consulta SQL
            sql = f"""
                SELECT 
                    "codigo-serial" AS Codigo,
                    "version-firmware" AS Firmware,
                    "comunicacion-232" AS "Comunicación232",
                    "prueba-leds" AS LED,
                    "prueba-lcds" AS LCDS,
                    "prueba-botones" AS Botones,
                    "prueba-entradas-digitales" AS Entradas,
                    fecha AS Fecha
                FROM "{table_name}"
                WHERE {where_str}
                ORDER BY fecha DESC
                {limit_clause};
            """

            print("Ejecutando SQL:", sql)
            print("Con valores:", values)

            cursor.execute(sql, tuple(values))
            rows = cursor.fetchall()

            # Retornar registros como lista de diccionarios
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"Error al obtener registros desde la base de datos: {e}")
            return []


    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            print("Conexión cerrada.")

# --- Ejemplo de uso ---
if __name__ == "__main__":
    db = SQLiteDatabase()

    # Ruta del archivo SQLite (se crea automáticamente si no existe)
    db_path = "C:/NidecDB/nidec-pentair-tester.db"
    table_name = '"pentair-tester-registers"'

    db.create_connection(db_path)
    #db.create_table(table_name)

    # # --- Insertar registros de prueba ---
    # registros_prueba = [
    #     {
    #         "id_prueba": 1,
    #         "id_pieza_ok": 10,
    #         "id_pieza_ng": 2,
    #         "sensores_resorte_a": "OK",
    #         "sensores_resorte_b": "OK",
    #         "inspeccion_visual": "Pieza correcta",
    #         "resultado": "Aprobado",
    #         "fecha": "2025-10-02 10:00:00"
    #     },
    #     {
    #         "id_prueba": 2,
    #         "id_pieza_ok": 8,
    #         "id_pieza_ng": 1,
    #         "sensores_resorte_a": "NG",
    #         "sensores_resorte_b": "NG",
    #         "inspeccion_visual": "Pieza con defecto visual",
    #         "resultado": "Rechazado",
    #         "fecha": "2025-10-02 11:30:00"
    #     }
    # ]

    # for registro in registros_prueba:
    #     db.insert_multiple_columns(table_name, registro)

    # --- Leer registros ---
    db.read_data(table_name)

    # --- Obtener el último ---
    db.get_last_record(table_name)

    # --- Cerrar conexión ---
    db.close_connection()
