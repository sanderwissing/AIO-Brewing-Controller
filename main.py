import lvgl as lv
import network
import time

from model import BrewingModel
from controller import BrewingController
from gui import BrewingGUI, show_splash_screen
from actuators import heater_on, heater_off
from touch import init_touch, touch_detected, handle_touch_event

# --- Wi-Fi Setup ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"Connecting to {ssid}...")
        wlan.connect(ssid, password)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print("✅ Wi-Fi connected:", wlan.ifconfig())
    else:
        print("❌ Failed to connect to Wi-Fi")

SSID = "YourNetworkName"
PASSWORD = "YourPassword"
connect_wifi(SSID, PASSWORD)

# --- LVGL Init ---
lv.init()

# Initialize display and GT911 touch controller here
# import ili9341_driver
# import gt911_driver
# ili9341_driver.init()
# gt911_driver.init()

init_touch()  # 🖐️ Touch controller scaffold initialized

# --- Brewing System Init ---
model = BrewingModel()
gui = BrewingGUI(model)
controller = BrewingController(model, gui)

# --- Splash Screen ---
show_splash_screen("S:/splash.bmp")  # Replace with actual image path

# --- Main Control Loop ---
def main_loop():
    while True:
        model.update_temperature()
        pid_output = model.get_heater_output()

        # Respect GUI heater toggle and heating flag
        if model.heater_enabled and model.heating_on and pid_output > 0:
            heater_on(pid_output)
        else:
            heater_off()

        # Update GUI visuals
        gui.update(
            temp=model.temperature,
            setpoint=model.setpoint,
            heater=pid_output,
            pump=model.pump_on,
            stage=model.stage
        )

        # Handle touch input
        if touch_detected():
            handle_touch_event()

        time.sleep_ms(100)

main_loop()