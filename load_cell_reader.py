import serial
import time
import json
import threading

class LoadCellreader:
    def __init__(self, com: str, baud_rate: int) -> None:
        self.ser = serial.Serial(com, baud_rate, timeout=2)
        self.ser_buffer = b''
        self.read_thread = None
        self.running = False

    def callback(self, msg: str):
        print(msg)

    def continuously_read(self):
        while self.running:
            buffer = self.ser.read_until(expected=b'\n')
            if not buffer:
                continue
            values_decoded = buffer.decode()
            # try:
            #     val_map = json.loads(values_decoded)
            #     self.callback(val_map)
            # except:
            self.callback(values_decoded)

    def start(self):
        self.setAutomaticMode()
        if not self.read_thread:
            self.running = True
            self.read_thread = threading.Thread(target=self.continuously_read)
            self.read_thread.start()
    
    def setAutomaticMode(self):
        print("Set Mode Load cell") 

        if not self.ser or not self.ser.is_open:
            raise Exception("Error Load Cell not connected")

        try:
            self.ser_buffer = self.ser.read_all()
            # calibrate
            self.ser.write(b'ma')
            time.sleep(0.2)
            
            self.ser_buffer = self.ser.read_all()

        except:
            raise Exception("Error connecting with Load Cell")
        
        return self.ser_buffer.decode()

    def isConnected(self):
        return (self.ser != None and self.ser.is_open)
    
    def disconnect(self):
        self.ser.close()
        if self.read_thread:
            self.running = False
            self.read_thread.join()
            self.read_thread = None
    
    def readBuffer(self):
        return self.ser.read_all()

    def get_current_force(self):
        try:
            self.ser.write(b'g')
            time.sleep(0.1)
            current_values = self.ser.readline()
            values = current_values.decode()
            val_map = json.loads(values)
        
            print(f"Force data: {val_map}")
            return val_map["calculatedWeight"]
        except:
            return None 

    def calibrate_lc(self, weigth_kg: float = 1.0):
        print("Calibrate Load cell") 

        if not self.ser or not self.ser.is_open:
            raise Exception("Error Load Cell not connected")

        try:
            self.ser_buffer = self.ser.read_all()
            # calibrate
            self.ser.write(b'c')
            time.sleep(0.2)
            self.ser.write(f'{weigth_kg}'.encode())
            time.sleep(0.2)
            
            self.ser_buffer = self.ser.read_all()

        except:
            raise Exception("Error connecting with Load Cell")
        
        return self.ser_buffer.decode()

    def tare_lc(self):
        print("Tare Load cell") 

        if not self.ser or not self.ser.is_open:
            raise Exception("Error Load Cell not connected")

        try:
            self.ser_buffer = self.ser.read_all()

            #tare
            self.ser.write(b't')
            time.sleep(0.2)
            
            self.ser_buffer = self.ser.read_all()

        except:
            raise Exception("Error connecting with Load Cell")
        
        return self.ser_buffer.decode()

    def connect_lc(self, event=None):
        if self.ser and self.ser.is_open:
            self.ser.close()

        try:
            # try to connect serial force sensor
            self.ser = serial.Serial(self.com, self.baud_rate, timeout = 2)  # open serial port

            init_message =  self.ser.read_all()

        except:
            raise Exception("Error connecting with Load Cell")
        
        return init_message.decode()
    

if __name__ == '__main__':
    
    SENSOR_COM = 'COM4'
    SERSOR_BR = 115200

    try:
        # try to connect serial force sensor
        ser = LoadCellreader(SENSOR_COM, SERSOR_BR)  # open serial port
        ser.start()

        # buffer = ser.readBuffer()
    except:
        pass
    input()