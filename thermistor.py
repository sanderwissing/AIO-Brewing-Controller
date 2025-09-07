from machine import ADC, Pin
from math import log
import ujson

class ThermistorReader:
    def __init__(self, adc_pin=1):
        self.adc = ADC(Pin(adc_pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)

        self.series_resistor = 10000.0
        self.nominal_resistance = 10000.0
        self.nominal_temp = 25.0
        self.beta = 3950.0
        self.calibration_offset = self.load_calibration()

    def read_temperature(self):
        raw = self.adc.read()
        voltage = raw / 4095.0 * 3.3
        resistance = self.series_resistor * (3.3 / voltage - 1.0)

        lnR = log(resistance / self.nominal_resistance)
        tempK = 1.0 / (lnR / self.beta + 1.0 / (self.nominal_temp + 273.15))
        tempC = tempK - 273.15
        return tempC + self.calibration_offset

    def load_calibration(self):
        try:
            with open("calibration.json", "r") as f:
                data = ujson.load(f)
                return data.get("offset", 0.0)
        except:
            return 0.0

    def save_calibration(self, offset):
        self.calibration_offset = offset
        with open("calibration.json", "w") as f:
            ujson.dump({"offset": offset}, f)