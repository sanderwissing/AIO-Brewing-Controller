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
        self.sensor.calibration_offset = offset

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

    def auto_tune_pid(self, relay_amplitude=10.0, n_cycles=5):
        """
        Simple relay-based PID auto-tune. Applies relay to heater and analyzes oscillation.
        relay_amplitude: temperature deviation to trigger relay
        n_cycles: number of oscillation cycles to observe
        """
        import time
        print("Starting PID auto-tune...")
        original_setpoint = self.setpoint
        self.setpoint = self.temperature + relay_amplitude
        self.heater_enabled = True
        self.heating_on = True
        relay_high = True
        t_high = []
        t_low = []
        last_switch_time = time.ticks_ms()
        cycle_count = 0
        temp_history = []
        while cycle_count < n_cycles:
            temp = self.sensor.read_temperature()
            temp_history.append(temp)
            if relay_high and temp >= original_setpoint + relay_amplitude:
                self.heating_on = False
                relay_high = False
                t_high.append(time.ticks_diff(time.ticks_ms(), last_switch_time)/1000.0)
                last_switch_time = time.ticks_ms()
                cycle_count += 1
                print(f"Relay LOW, cycle {cycle_count}")
            elif not relay_high and temp <= original_setpoint - relay_amplitude:
                self.heating_on = True
                relay_high = True
                t_low.append(time.ticks_diff(time.ticks_ms(), last_switch_time)/1000.0)
                last_switch_time = time.ticks_ms()
                print(f"Relay HIGH, cycle {cycle_count}")
            time.sleep(0.5)
        # Calculate period and amplitude
        avg_period = (sum(t_high) + sum(t_low)) / n_cycles
        amplitude = relay_amplitude
        Ku = (4.0 * amplitude) / (3.1415 * (max(temp_history) - min(temp_history)))
        Tu = avg_period
        # Ziegler-Nichols tuning
        kp = 0.6 * Ku
        ki = 1.2 * Ku / Tu
        kd = 0.075 * Ku * Tu
        self.pid.kp = kp
        self.pid.ki = ki
        self.pid.kd = kd
        self.setpoint = original_setpoint
        self.heater_enabled = False
        self.heating_on = False
        print(f"Auto-tune complete. New PID: Kp={kp:.2f}, Ki={ki:.2f}, Kd={kd:.2f}")
        return kp, ki, kd