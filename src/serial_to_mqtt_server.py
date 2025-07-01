import serial
import platform
import sys
import json 
import paho.mqtt.client as mqtt
import signal

machine = platform.machine().lower()
if machine == "aarch64":
    product_file_path = "/etc/product"
else:
    product_file_path = "product"

class MQTTBridge:
    SLIP_END = b'\xC0'
    SLIP_ESC = b'\xDB'
    SLIP_ESC_END = b'\xDC'
    SLIP_ESC_ESC = b'\xDD'
    STX = 0x76
    ETX = 0x3E

    act_id = {"ConveyorBelt":0x10, "ServoIn":0x11, "ServoMake":0x12, "ServoSort":0x13, "Indicator":0x14}
    sensor_id = {"Encoder": 0x20, "ServoIn":0x21, "ServoMake":0x22, "ServoSort":0x23, "PhotoGroup":0x24, "PhotoSort1":0x25, "PhotoSort2":0x26, "Inductive":0x27, "SwitchStart":0x28, "SwitchStop": 0x29}
    indicator_table = {"red":0x01, "yellow": 0x02, "green": 0x03}
    servo_name_table = {"sorting":"ServoSort","feeding":"ServoIn","processing":"ServoMake"}
    servo_value_table = {
        "sorting-hit"  : 0,
        "sorting-normal"  : 1,
        "feeding-load"   : 0,
        "feeding-supply" : 1,
        "processing-up"  : 0,
        "processing-down": 1
    }
    convey_step = {"0" : [0x00, 0x00], "1" : [0xFF, 0xFF], "2" : [0xE6, 0x66], "3" : [0xCC, 0xCD]}

    with open(product_file_path, 'r') as file:
        BROKER_DOMAIN = None
        DEV_NUM = None
        DEV_NAME = None
        INSITUTION_NAME = None
        for line in file:
            line = line.strip()
            if line.startswith('BROKER_DOMAIN='):
                BROKER_DOMAIN = line.split('=')[1].strip()
            if line.startswith('DEV_NUM='):
                DEV_NUM = line.split('=')[1].strip()
            if line.startswith('DEVICE_NAME='):
                DEV_NAME = line.split('=')[1].strip()
            if line.startswith('INSITUTION_NAME='):
                INSITUTION_NAME = line.split('=')[1].strip()
        if BROKER_DOMAIN is None:
            raise "[Error] There is no product file. Please make sure the device has product info"
    
    crc16_table = [
        0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
        0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
        0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
        0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
        0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
        0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
        0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
        0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
        0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
        0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
        0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
        0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
        0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
        0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
        0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
        0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
        0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
        0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
        0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
        0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
        0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
        0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
        0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
        0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
        0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
        0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
        0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
        0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
        0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
        0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
        0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
        0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
    ]
    
    def __init__(self):
        self.Serial = serial.Serial(
            port="/dev/ttyACM0",
            baudrate=115200,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1e-3,
        )
        self.receiver = None
        self.sender = None
        self.loop = True 
        self._client = mqtt.Client()
        signal.signal(signal.SIGINT, self._signal_handler)
        self.TOPIC_HEADER = MQTTBridge.DEV_NAME+"/"+MQTTBridge.INSITUTION_NAME+MQTTBridge.DEV_NUM
        self._client.on_connect = self._on_connect 
        self._client.on_message = self._on_message
        self._client.connect(MQTTBridge.BROKER_DOMAIN)
        self._client.loop_start()

    def __del__(self):
        self.Serial.close()

    def _signal_handler(self, signal, frame):
        self._client.disconnect() 
        sys.exit()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._client.subscribe(self.TOPIC_HEADER+"/+/indicator")
            self._client.subscribe(self.TOPIC_HEADER+"/+/+/set")
            self._client.subscribe(self.TOPIC_HEADER+"/+/+/step")

    def _on_message(self, client, userdata, message):
        payload = message.payload.decode('utf-8')
        try:
            serial_data = [self.STX]
            if message.topic.find('indicator') != -1 and message.topic.find('safety') != -1:
                serial_data.append(self.act_id["Indicator"])
                serial_data.append(0x01)
                serial_data.append(0x00 if payload == "off" else self.indicator_table[payload])
            elif message.topic.find('step') != -1 and message.topic.find('transfer') != -1:
                serial_data.append(self.act_id["ConveyorBelt"])
                serial_data.append(0x03)
                serial_data.append(0x01)
                serial_data.extend(self.convey_step[payload])
            elif message.topic.find('set') != -1 :
                block = message.topic.split('/')[2]
                serial_data.append(self.act_id[self.servo_name_table[block]])
                serial_data.append(0x01)
                serial_data.append(self.servo_value_table[block+"-"+payload])
            crc_value = self._crc16_modbus(bytes(serial_data[1:]))
            serial_data.append(crc_value >> 8)
            serial_data.append(crc_value & 0x0FF)
            serial_data.append(self.ETX)
            self._slip_uart_write(serial_data)
        except Exception as e:
            print("Wrong topic & value received")
            print(e)

    def _crc16_modbus(self, data, init_crc=0xFFFF):
        crc = [init_crc >> 8, init_crc & 0xFF]
            
        for byte in data:
            tmp = MQTTBridge.crc16_table[crc[0] ^ byte]
            crc[0] = (tmp & 0xFF) ^ crc[1]
            crc[1] = tmp>>8
        
        return (crc[0]|crc[1]<<8)

    def _slip_uart_write(self, value):
        data = bytes(json.dumps(value).encode())
        self.Serial.write(self.SLIP_END + data.replace(self.SLIP_ESC, self.SLIP_ESC_ESC).replace(self.SLIP_END, self.SLIP_ESC + self.SLIP_ESC_END)+self.SLIP_END)

    def _slip_uart_read(self):
        started = False
        skip = False 
        data = b''
        while True:
            char = self.Serial.read(1)
            if char == b'':
                break
            if char == self.SLIP_END:
                if not started:
                    if data:
                        data = b''
                    started = True
                else:
                    data.replace(self.SLIP_ESC + self.SLIP_ESC_END, self.SLIP_END).replace(self.SLIP_ESC + self.SLIP_ESC_ESC, self.SLIP_ESC)
                    break
            else:
                if started:
                    data += char
        try:
            return json.loads(data.decode())
        except:
            return None
                
    def _buf(self, sender, message):
        pass
        
    def _loop(self):
        data = []
        send_data = []

        while True:
            try:
                data.clear()
                send_data.clear()

                while self.loop:
                    try:
                        recv_data = self._slip_uart_read()
                        if recv_data[0] == self.STX and recv_data[-1] == self.ETX:
                            packet_crc = (recv_data[-3]<<8)|recv_data[-2]
                            calc_crc = self._crc16_modbus(recv_data[1:-3])
                            if packet_crc == calc_crc:
                                packet_id = recv_data[1]
                                if packet_id == self.sensor_id["Encoder"]:
                                    self._client.publish(self.TOPIC_HEADER+"/transfer/encoder",(recv_data[3] << 8) + recv_data[4], 0)
                                    break
                                elif packet_id == self.sensor_id["ServoIn"]:
                                    self._client.publish(self.TOPIC_HEADER+"/feeding/servo/state", "supply" if recv_data[3] else "load", 0)
                                    break
                                elif packet_id == self.sensor_id["ServoMake"]:
                                    self._client.publish(self.TOPIC_HEADER+"/processing/servo/state", "down" if recv_data[3] else "up", 0)
                                    break
                                elif packet_id == self.sensor_id["ServoSort"]:
                                    self._client.publish(self.TOPIC_HEADER+"/sorting/servo/state", "normal" if recv_data[3] else "hit", 0)
                                    break
                                elif packet_id == self.sensor_id["PhotoGroup"]:
                                    self._client.publish(self.TOPIC_HEADER+"/feeding/photo", "exist" if recv_data[3] else "non-exist", 0) 
                                    self._client.publish(self.TOPIC_HEADER+"/processing/photo", "exist" if recv_data[5] else "non-exist", 0) 
                                    self._client.publish(self.TOPIC_HEADER+"/sorting/photo", "exist" if recv_data[4] else "non-exist", 0) 
                                    break
                                elif packet_id == self.sensor_id["PhotoSort1"]:
                                    self._client.publish(self.TOPIC_HEADER+"/sorting/hit_count", "count", 0) 
                                    break
                                elif packet_id == self.sensor_id["PhotoSort2"]:
                                    self._client.publish(self.TOPIC_HEADER+"/sorting/normal_count", "count", 0) 
                                    break
                                elif packet_id == self.sensor_id["Inductive"]:
                                    self._client.publish(self.TOPIC_HEADER+"/sorting/inductive", "metal" if recv_data[3] else "non-metal", 0)  
                                    break
                                elif packet_id == self.sensor_id["SwitchStart"]:
                                    self._client.publish(self.TOPIC_HEADER+"/safety/sw_start", "active" if recv_data[3] else "deactive", 0)  
                                    break
                                elif packet_id == self.sensor_id["SwitchStop"]:
                                    self._client.publish(self.TOPIC_HEADER+"/safety/sw_stop", "stop" if recv_data[3] else "running", 0)  
                                    break
                    except TypeError:
                        pass
            except KeyboardInterrupt:
                self.stop()
                sys.exit()
        
    def start(self):
        self._loop()
        
    def stop(self):
        self.thread_loop = False
        self.thread.join()

print("[INFO] MQTT Bridge loop is running...")
mqtt_bridge = MQTTBridge()
mqtt_bridge.start()