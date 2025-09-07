# touch.py — GT911 touch controller scaffold

import machine
import time

# --- I2C Setup (adjust pins as needed) ---
i2c = machine.I2C(1, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000)

GT911_ADDR = 0x5D  # Default I2C address
TOUCH_STATUS_REG = 0x814E
TOUCH_DATA_REG = 0x8150

def init_touch():
    # Optional: reset sequence or config
    print("🖐️ GT911 touch controller initialized")

def touch_detected():
    try:
        status = i2c.readfrom_mem(GT911_ADDR, TOUCH_STATUS_REG, 1)[0]
        return status & 0x01  # Bit 0 indicates touch
    except Exception as e:
        print(f"⚠️ Touch read error: {e}")
        return False

def get_touch_coordinates():
    try:
        data = i2c.readfrom_mem(GT911_ADDR, TOUCH_DATA_REG, 4)
        x = data[1] << 8 | data[0]
        y = data[3] << 8 | data[2]
        return (x, y)
    except Exception as e:
        print(f"⚠️ Coordinate read error: {e}")
        return None

def handle_touch_event():
    coords = get_touch_coordinates()
    if coords:
        x, y = coords
        print(f"📍 Touch at ({x}, {y})")
        # TODO: Dispatch to LVGL or GUI handler