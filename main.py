import lvgl as lv
import network
import time
import controller
import gui
import model
import touch
import _thread
from webserver import start_web_server  # 👈 New module

# Initialize LVGL
lv.init()

# Connect to Wi-Fi
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect("your-ssid", "your-password")

print("Connecting to Wi-Fi...")
while not sta_if.isconnected():
    time.sleep(0.5)

ip = sta_if.ifconfig()[0]
print(f"✅ Connected to Wi-Fi. IP address: {ip}")

# Initialize model and GUI
brew_model = model.BrewModel()
gui.init_gui(brew_model)

# Start touch input (GT911)
touch.init_touch()

# Start control loop
_thread.start_new_thread(controller.run_loop, (brew_model,))

# Start web server for PID tuning and actuator control
_thread.start_new_thread(start_web_server, (brew_model,))

# Show splash screen (optional)
gui.show_splash_screen()

# Main loop for LVGL tick and task handling
while True:
    time.sleep(0.05)
    lv.tick_inc(50)
    lv.task_handler()
