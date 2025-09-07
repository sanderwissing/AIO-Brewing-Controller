# touch.py — Fixed GT911 touch controller with LVGL integration

import machine
import time
import lvgl as lv

# --- I2C Setup (adjust pins as needed) ---
i2c = machine.I2C(1, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000)

GT911_ADDR = 0x5D  # Default I2C address
TOUCH_STATUS_REG = 0x814E
TOUCH_DATA_REG = 0x8150

class GT911TouchDriver:
    def __init__(self):
        self.last_x = 0
        self.last_y = 0
        self.pressed = False
        
        # Create LVGL input device
        self.indev = lv.indev_drv_t()
        self.indev.init()
        self.indev.type = lv.INDEV_TYPE.POINTER
        self.indev.read_cb = self._read_touch
        self.touch_device = lv.indev_drv_register(self.indev)
        
        print("🖐️ GT911 touch controller initialized with LVGL")

    def _read_touch(self, indev_drv, data):
        """LVGL touch read callback"""
        try:
            # Read touch status
            status = i2c.readfrom_mem(GT911_ADDR, TOUCH_STATUS_REG, 1)[0]
            touch_detected = bool(status & 0x01)
            
            if touch_detected:
                # Read coordinates
                coord_data = i2c.readfrom_mem(GT911_ADDR, TOUCH_DATA_REG, 4)
                x = coord_data[1] << 8 | coord_data[0]
                y = coord_data[3] << 8 | coord_data[2]
                
                # Transform coordinates if needed (depends on your display orientation)
                # For 480x480 display, you might need to adjust these values
                x = min(max(x, 0), 479)
                y = min(max(y, 0), 479)
                
                self.last_x = x
                self.last_y = y
                self.pressed = True
                
                # Set LVGL data
                data.point.x = x
                data.point.y = y
                data.state = lv.INDEV_STATE.PRESSED
                
                # Clear touch status register
                i2c.writeto_mem(GT911_ADDR, TOUCH_STATUS_REG, bytes([0]))
                
            else:
                # No touch detected
                data.point.x = self.last_x
                data.point.y = self.last_y
                data.state = lv.INDEV_STATE.RELEASED
                self.pressed = False
                
        except Exception as e:
            print(f"⚠️ Touch read error: {e}")
            # Return released state on error
            data.point.x = self.last_x
            data.point.y = self.last_y
            data.state = lv.INDEV_STATE.RELEASED
            self.pressed = False
        
        return False  # No buffering needed

    def is_pressed(self):
        """Check if touch is currently pressed"""
        return self.pressed
    
    def get_coordinates(self):
        """Get last touch coordinates"""
        return (self.last_x, self.last_y)

# Global touch driver instance
touch_driver = None

def init_touch():
    """Initialize touch controller and return driver instance"""
    global touch_driver
    try:
        touch_driver = GT911TouchDriver()
        return touch_driver
    except Exception as e:
        print(f"❌ Failed to initialize touch controller: {e}")
        return None

def touch_detected():
    """Check if touch is detected (for compatibility)"""
    if touch_driver:
        return touch_driver.is_pressed()
    return False

def get_touch_coordinates():
    """Get touch coordinates (for compatibility)"""
    if touch_driver:
        return touch_driver.get_coordinates()
    return None

def handle_touch_event():
    """Handle touch event (legacy function - not needed with LVGL integration)"""
    coords = get_touch_coordinates()
    if coords:
        x, y = coords
        print(f"📍 Touch at ({x}, {y})")

def scan_i2c():
    """Scan I2C bus for GT911"""
    print("🔍 Scanning I2C bus...")
    devices = i2c.scan()
    if devices:
        print(f"Found I2C devices: {[hex(device) for device in devices]}")
        if GT911_ADDR in devices:
            print(f"✅ GT911 found at address {hex(GT911_ADDR)}")
        else:
            print(f"⚠️ GT911 not found at expected address {hex(GT911_ADDR)}")
    else:
        print("❌ No I2C devices found")
    return devices