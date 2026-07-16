import serial
from typing import Optional

class SerialDevice:
    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None

    def connect(self):
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout
            )
            print(f"Connected to {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print(f"Disconnected from {self.port}")

    def send_command(self, command: str) -> Optional[str]:
        if not self.serial_connection or not self.serial_connection.is_open:
            print(f"Not connected to {self.port}")
            return None
        try:
            command_bytes = bytes.fromhex(command)
            self.serial_connection.write(command_bytes)
            return self.read_response()
        except Exception as e:
            print(f"Failed to send command: {e}")
            return None

    def read_response(self) -> Optional[str]:
        try:
            response = self.serial_connection.read(256)  # Leer hasta 256 bytes o ajustar según sea necesario
            return response.hex().upper()
        except Exception as e:
            print(f"Failed to read response: {e}")
            return None

    def calculate_checksum(self, packet_bytes):
        """
        Calcula el checksum Pentair.

        packet_bytes:
            Lista de bytes comenzando desde 0xA5
        """

        checksum = sum(packet_bytes)

        high = (checksum >> 8) & 0xFF
        low = checksum & 0xFF

        return high, low
    
    def build_lcd_text(self,text):
        """
        Construye un comando Write LCD Text.

        Ejemplos:

            build_lcd_text("1234")
            build_lcd_text("HELP")
            build_lcd_text("8888")
        """

        # El LCD únicamente acepta 4 caracteres
        text = text[:4].ljust(4)

        ascii_bytes = [ord(c) for c in text]

        packet = [
            0xA5,
            0x00,
            0x60,
            0x10,
            0x0D,
            0x07,
            0xD0,
            0x5D,
            0x04,
            *ascii_bytes
        ]

        high, low = self.calculate_checksum(packet)

        full_packet = [
            0xFF,
            0x00,
            0xFF,
            *packet,
            high,
            low
        ]

        return ''.join(f'{b:02X}' for b in full_packet)

if __name__ == "__main__":
    # Crear una instancia del dispositivo serial
    device = SerialDevice(port='COM8', baudrate=9600, timeout=1)

    # Conectar al dispositivo
    device.connect()

    # Enviar un comando al dispositivo
    command = 'FF00FFA50060100D04D05101010249'  # Comando en formato hexadecimal
    response = device.send_command(command)

    # # Enviar un comando al dispositivo
    # command = 'FF00FFA50060100D07D05D0438383838033A'  # Comando en formato hexadecimal
    # response = device.send_command(command)

    # command = 'FF00FFA50060100D07D05D04333333330326'
    # response = device.send_command(command) #Escribir unicamente 3 


    # command = 'FF00FFA50060100D07D05D0435353535032E'
    # response = device.send_command(command) #Escribir unicamente 5
    
    # command = 'FF00FFA50060100D07D05D04363636360332'
    # response = device.send_command(command) #Escribir unicamente 6 


    # command = 'FF00FFA50060100D07D05D0448484848037A'
    # response = device.send_command(command) #Escribir unicamente LETRA H

    # command = 'FF00FFA50060100D07D05D044F4F4F4F0396'
    # response = device.send_command(command) #Escribir unicamente LETRA O


    command = 'FF00FFA50060100D07D05D04434343430366'
    response = device.send_command(command) #Escribir unicamente LETRA C

    #  # Enviar un comando al dispositivo
    # command = 'FF00FFA50060100D07D05D043333333302F4'  # Comando en formato hexadecimal
    # response = device.send_command(command)

    # # Enviar un comando al dispositivo
    # command = 'FF00FFA50060100D04D05E013F0294'  # Comando en formato hexadecimal
    # response = device.send_command(command)

    # # Enviar un comando al dispositivo
    # command = 'FF00FFA50060100D05D05B0203FF0356'  # Comando en formato hexadecimal
    # response = device.send_command(command)


    

    # Mostrar la respuesta recibida
    if response:
        print(f"Response: {response}")
    else:
        print("No response received or failed to read response.")

    # Desconectar el dispositivo
    device.disconnect()