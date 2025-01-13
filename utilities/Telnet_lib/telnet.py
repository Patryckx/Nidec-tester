import telnetlib
import time


class TelnetClient:
    def __init__(self, host, port, timeout=10):
        """
        Inicializa la clase para la conexión Telnet.
        :param host: Dirección IP o hostname del dispositivo.
        :param port: Puerto Telnet del dispositivo.
        :param timeout: Tiempo máximo de espera para respuestas.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.connection = None

    def connect(self):
        """
        Establece una conexión Telnet con el dispositivo.
        """
        try:
            self.connection = telnetlib.Telnet(self.host, self.port, self.timeout)
            print(f"Conexión establecida con {self.host}:{self.port}")
        except Exception as e:
            raise ConnectionError(f"No se pudo conectar a {self.host}:{self.port}. Error: {e}")

    def send_data(self, data):
        """
        Envía datos al dispositivo.
        :param data: Cadena de datos a enviar.
        """
        if not self.connection:
            raise ConnectionError("No hay una conexión activa.")
        try:
            self.connection.write(data.encode('ascii') + b'\n')
            print(f"Datos enviados: {data}")
        except Exception as e:
            raise RuntimeError(f"Error al enviar datos: {e}")

    def read_data(self, wait_time=1):
        """
        Lee datos recibidos del dispositivo.
        :param wait_time: Tiempo de espera antes de leer.
        :return: Respuesta del dispositivo como cadena.
        """
        if not self.connection:
            raise ConnectionError("No hay una conexión activa.")
        try:
            time.sleep(wait_time)  # Espera para recibir respuesta
            response = self.connection.read_very_eager().decode('ascii')
            print(f"Datos recibidos: {response}")
            return response
        except Exception as e:
            raise RuntimeError(f"Error al leer datos: {e}")

    def close_connection(self):
        """
        Cierra la conexión Telnet.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            print("Conexión cerrada.")

if __name__ == "__main__":
    # Configuración del dispositivo para pruebas
    host = "192.168.1.121"  # Reemplaza con la IP del dispositivo
    port = 8500               # Puerto Telnet estándar

    # Crear una instancia del cliente Telnet
    client = TelnetClient(host, port)

    try:
        # Conectar al dispositivo
        client.connect()
        
        # Enviar un comando de prueba
        #client.send_data("comando_ejemplo")
        while True:
            # Leer la respuesta
            response = client.read_data()
            print(f"Respuesta del dispositivo: {response}")

            if response==client.timeout():
                break
    finally:
        # Cerrar la conexión
        client.close_connection()