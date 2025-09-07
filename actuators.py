from machine import Pin, PWM

# --- Heater Setup ---
heater_pin = Pin(9, Pin.OUT)
heater_pwm = PWM(heater_pin, freq=1000)
heater_pwm.duty(0)

# --- Pump Setup ---
pump_pin = Pin(10, Pin.OUT)
pump_pin.value(0)

# --- Heater Control ---
def heater_on(pid_output):
    """
    Accepts PID output (0–100) and sets PWM duty accordingly.
    """
    duty = int(pid_output / 100 * 1023)
    heater_pwm.duty(duty)
    print(f"🔥 Heater ON — PID: {pid_output:.1f} → Duty: {duty}/1023")

def heater_off():
    heater_pwm.duty(0)
    print("🧊 Heater OFF")

# --- Pump Control ---
def pump_on():
    pump_pin.value(1)
    print("💧 Pump ON")

def pump_off():
    pump_pin.value(0)
    print("🚫 Pump OFF")