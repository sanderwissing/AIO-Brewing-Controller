from thermistor import ThermistorReader
from simple_pid import PID
from machine import Pin, PWM

class BrewingModel:
    def __init__(self):
        self.sensor = ThermistorReader(adc_pin=1)
        self.temperature = self.sensor.read_temperature()
        self.setpoint = 65.0

        self.pid = PID(2.0, 0.1, 0.05, setpoint=self.setpoint)
        self.pid.output_limits = (0, 100)

        self.pump_on = False
        self.heating_on = False
        self.heater_enabled = False
        self.stage = "Idle"

        self.pump_pin = Pin(10, Pin.OUT)
        self.heater_pwm = PWM(Pin(9), freq=1000)
        self.heater_pwm.duty(0)

    def update_temperature(self):
        temp = self.sensor.read_temperature()
        if 0.0 <= temp <= 100.0:
            self.temperature = temp
        else:
            print(f"⚠️ Sensor out of range: {temp:.2f}°C — disabling heating")
            self.temperature = temp
            self.heating_on = False
            self.heater_enabled = False
            self.heater_pwm.duty(0)

    def get_heater_output(self):
        if self.heater_enabled and self.heating_on:
            power = self.pid(self.temperature)
            duty = int(power / 100 * 1023)
            self.heater_pwm.duty(duty)
            return power
        else:
            self.heater_pwm.duty(0)
            return 0

    def set_target_temperature(self, temp):
        self.setpoint = temp
        self.pid.setpoint = temp

    def set_calibration_offset(self, offset):
        self.sensor.save_calibration(offset)

    def toggle_pump(self):
        self.pump_on = not self.pump_on
        self.pump_pin.value(1 if self.pump_on else 0)

    def toggle_heater_enabled(self):
        self.heater_enabled = not self.heater_enabled
        if not self.heater_enabled:
            self.heating_on = False
            self.heater_pwm.duty(0)

    def toggle_heating(self):
        self.heating_on = not self.heating_on
        if not self.heating_on:
            self.heater_pwm.duty(0)

    def start_brewing(self):
        self.stage = "Heating"