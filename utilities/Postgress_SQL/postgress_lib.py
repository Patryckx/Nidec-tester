import psycopg2
from psycopg2 import OperationalError, Error
from psycopg2.extras import RealDictCursor

class PostgresDatabase:
    def __init__(self):
        self.connection = None

    def create_connection(self, host, database, port=5432):
        """Establece una conexión a la base de datos PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=host,
                database=database,
                user="smitech",
                password="5m1t3ch",
                port=port,
                cursor_factory=RealDictCursor
            )
            print("Conexión exitosa a la base de datos PostgreSQL.")
            return self.connection
        except OperationalError as e:
            print(f"Error al conectar a PostgreSQL: {e}")
            return None

    def create_table(self, table_name):
        """Crea una tabla si no existe"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        tag_name VARCHAR(50) NOT NULL,
                        value REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            self.connection.commit()
            print(f"Tabla '{table_name}' creada/verificada.")
        except Error as e:
            print(f"Error al crear tabla: {e}")

    def insert_data(self, table_name, tag, value):
        """Inserta datos en una tabla específica"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    INSERT INTO {table_name} (tag_name, value)
                    VALUES (%s, %s)
                """, (tag, value))
            self.connection.commit()
            print(f"Datos insertados en '{table_name}': Tag={tag}, Value={value}")
        except Error as e:
            print(f"Error al insertar datos: {e}")

    def insert_multiple_columns(self, table_name, data: dict):
        """Inserta datos en múltiples columnas"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return
        try:
            with self.connection.cursor() as cursor:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                values = tuple(data.values())
                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
            self.connection.commit()
            print(f"Datos insertados en '{table_name}': {data}")
        except Error as e:
            print(f"Error al insertar datos múltiples: {e}")

    def read_data(self, table_name):
        """Lee todos los registros de la tabla"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name}")
                records = cursor.fetchall()
                print(f"\nRegistros en '{table_name}':")
                for row in records:
                    print(row)
                return records
        except Error as e:
            print(f"Error al leer datos: {e}")
            return []
    def get_last_record(self, table_name):

        # ORDER BY Id DESC -> ordenar por fecha
        """Obtiene el último registro de la tabla basado en la fecha más reciente"""
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT * FROM {table_name}
                    ORDER BY fecha DESC
                    LIMIT 1
                """)
                record = cursor.fetchone()
                print(f"Último registro en '{table_name}': {record}")
                return record
        except Error as e:
            print(f"Error al obtener el último registro: {e}")
            return None
        
    def get_last_record_by_column_value(self, table_name, column_name, value):
        """
        Obtiene el último registro de la tabla filtrado por una columna específica,
        ordenado por la fecha más reciente (timestamp o columna de tipo TIMESTAMP WITH TIME ZONE).

        :param table_name: Nombre de la tabla
        :param column_name: Nombre de la columna por la cual filtrar
        :param value: Valor a buscar en la columna (texto, número, etc.)
        :return: Diccionario con el registro más reciente o None si no hay coincidencias
        """
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = f"""
                    SELECT *
                    FROM {table_name}
                    WHERE {column_name} = %s
                    ORDER BY fecha DESC
                    LIMIT 1
                """
                cursor.execute(sql, (value,))
                record = cursor.fetchone()

                if record:
                    print(f"Último registro con {column_name}='{value}': {record}")
                else:
                    print(f"No se encontró ningún registro con {column_name}='{value}'.")

                return record

        except Error as e:
            print(f"Error al obtener el último registro filtrado: {e}")
            return None
        
    def get_last_record_fields_by_column(self, table_name, column_name, value, fields):
        """
        Obtiene columnas específicas del último registro filtrado por una columna dada,
        ordenado por la fecha más reciente.

        :param table_name: Nombre de la tabla
        :param column_name: Columna por la que se filtra (ej. 'resultado', 'tag_name')
        :param value: Valor a buscar en la columna
        :param fields: Lista de columnas a devolver (ej. ['id_prueba', 'id_pieza_ok', 'id_pieza_ng'])
        :return: Diccionario con los campos solicitados o None
        """
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return None

        try:
            with self.connection.cursor() as cursor:
                columns_str = ', '.join(fields)
                sql = f"""
                    SELECT {columns_str}
                    FROM {table_name}
                    WHERE {column_name} = %s
                    ORDER BY fecha DESC
                    LIMIT 1
                """
                cursor.execute(sql, (value,))
                record = cursor.fetchone()
                if record:
                    print(f"Registro más reciente con {column_name}='{value}': {record}")
                else:
                    print(f"No se encontró registro con {column_name}='{value}'")
                return record
        except Error as e:
            print(f"Error al obtener registro filtrado: {e}")
            return None
        

    def get_last_record_fields_by_columns(self, table_name, conditions, fields):
        if not self.connection:
            print("No hay conexión a la base de datos.")
            return None

        try:
            with self.connection.cursor() as cursor:
                columns_str = ', '.join(fields)  #  sin comillas

                # Construir condiciones dinámicamente
                where_clauses = []
                values = []
                for col, val in conditions.items():
                    where_clauses.append(f"{col} = %s")
                    values.append(val)
                where_str = " AND ".join(where_clauses)

                print(f"Nombre real de la tabla: {repr(table_name)}")

                table_name = table_name.replace('"', '').strip()

                #  Nota: table_name sin comillas externas
                sql = f"""
                    SELECT {columns_str}
                    FROM "{table_name}"
                    WHERE {where_str}
                    ORDER BY fecha DESC
                    LIMIT 1
                """

                print("SQL ejecutado:", sql)
                cursor.execute(sql, tuple(values))
                record = cursor.fetchone()

                if not record:
                    print(f"No se encontró registro con {conditions}")
                    return None

                # columns = [desc[0] for desc in cursor.description]
                # record_dict = dict(zip(columns, record))

                print("Registro correcto:", record)
                return record

        except Exception as e:
            print(f"Error al obtener registro filtrado: {e}")
        return None


        
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            print("Conexión cerrada.")

# --- Ejemplo de uso ---
if __name__ == "__main__":
   
    db = PostgresDatabase()

    table_name = '"9748-registers"'  # asegúrate que sea el nombre real de tu tabla se añaden comillas debido a politica de postgresss

    db.create_connection(
        host='localhost',
        database='MMI',
        port=5432
    )

    # --- Insertar registros de prueba ---
    registros_prueba = [
        {
            "id_prueba": 1,
            "id_pieza_ok": 10,
            "id_pieza_ng": 2,
            "sensores_resorte_a": "OK",
            "sensores_resorte_b": "OK",
            "inspeccion_visual": "Pieza correcta",
            "resultado": "Aprobado",
            "fecha": "2025-10-02 10:00:00+00"
        },
        {
            "id_prueba": 2,
            "id_pieza_ok": 8,
            "id_pieza_ng": 1,
            "sensores_resorte_a": "NG",
            "sensores_resorte_b": "NG",
            "inspeccion_visual": "Pieza con defecto visual",
            "resultado": "Rechazado",
            "fecha": "2025-10-02 11:30:00+00"
        }
    ]

    for registro in registros_prueba:
        db.insert_multiple_columns(table_name, registro)

    # --- Leer registros ---
    db.read_data(table_name)

    # --- Obtener el último ---
    db.get_last_record(table_name)

    # --- Cerrar conexión ---
    db.close_connection()
