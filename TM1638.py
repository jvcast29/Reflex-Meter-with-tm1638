from machine import Pin
import time

class TM1638:
    # Tabla de decodificación alfanumérica para cátodo común (Look-Up Table)
    FONT = {
        '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F, '4': 0x66,
        '5': 0x6D, '6': 0x7D, '7': 0x07, '8': 0x7F, '9': 0x6F,
        'A': 0x77, 'B': 0x7C, 'C': 0x39, 'D': 0x5E, 'E': 0x79,
        'F': 0x71, 'G': 0x3D, 'H': 0x76, 'I': 0x06, 'L': 0x38,
        'N': 0x37, 'O': 0x3F, 'P': 0x73, 'T': 0x31, 'U': 0x3E,
        ' ': 0x00, '-': 0x40, '!': 0x86
    }

    def __init__(self, stb_pin, clk_pin, dio_pin):
        self._stb = Pin(stb_pin, Pin.OUT)
        self._clk = Pin(clk_pin, Pin.OUT)
        self._dio = Pin(dio_pin, Pin.OUT)
        self._stb.on()
        self._clk.on()
        self.init()

    def init(self):
        self.clearDisplay()
        self.clearLeds()
        self.setBrightness(7)  # Brillo máximo por defecto
        self.displayText("HOLA    ")

    def setBrightness(self, brightness):
        if brightness > 7:
            brightness = 7
        elif brightness < 0:
            brightness = 0
        command = 0x88 | brightness
        self.sendCommand(command)

    def displayDigit(self, position, value):
        if 0 <= position < 8:
            seg = self.FONT.get(str(value).upper(), 0x00)
            self.sendData(position << 1, seg)

    def displayText(self, text):
        text_str = str(text)
        for i in range(8):
            if i < len(text_str):
                char = text_str[i]
                seg = self.FONT.get(char.upper(), 0x00)
            else:
                seg = 0x00
            self.sendData(i << 1, seg)

    def displayNumber(self, number):
        s_num = str(number)
        if len(s_num) < 8:
            s_num = (" " * (8 - len(s_num))) + s_num
        else:
            s_num = s_num[:8]
        self.displayText(s_num)

    def displayLed(self, led, state):
        if led < 0 or led >= 8:
            return
        self.sendData((led << 1) + 1, 0x01 if state else 0x00)

    def clearDisplay(self):
        for i in range(8):
            self.sendData(i << 1, 0x00)

    def clearLeds(self):
        for i in range(8):
            self.displayLed(i, False)

    def readKeys(self):
        keys = 0
        self._stb.off()
        self.sendByte(0x42)
        self._dio.init(Pin.IN)  # Cambiar a modo entrada
        for i in range(4):
            value = 0
            for j in range(8):
                self._clk.off()
                time.sleep_us(1)
                if (self._dio.value()):
                    value |= (1 << j)
                self._clk.on()
                time.sleep_us(1)
            keys |= (value << (i * 8))
        self._dio.init(Pin.OUT)  # Volver a salida
        self._stb.on()
        return keys

    def sendCommand(self, command):
        self._stb.off()
        self.sendByte(command)
        self._stb.on()

    def sendData(self, address, data):
        self.sendCommand(0x44)
        self._stb.off()
        self.sendByte(0xC0 | address)
        self.sendByte(data)
        self._stb.on()
        
    def sendByte(self, data):
        for _ in range(8):
            self._clk.off()
            self._dio.value(data & 0x01)
            time.sleep_us(1)
            self._clk.on()
            time.sleep_us(1)
            data >>= 1