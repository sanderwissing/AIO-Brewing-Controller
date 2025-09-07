# main.py - Complete async brewing controller with full feature set

import lvgl as lv
import network
import time
import uasyncio as asyncio

from model import BrewingModel
from controller import BrewingController
from gui import BrewingGUI, show_splash_screen
from actuators import heater_on, heater_off
from touch import init_touch, scan_i2c

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

# Initialize display driver here (uncomment and adjust for your display)
# import ili9341_driver
# ili9341_driver.init()

# --- Touch Controller Init ---
print("🖐️ Initializing touch controller...")

# Debug: Scan for I2C devices first
scan_i2c()

# Initialize touch controller (this now integrates with LVGL automatically)
touch_driver = init_touch()

if touch_driver:
    print("✅ Touch controller initialized successfully")
else:
    print("⚠️ Touch controller initialization failed - GUI will still work but no touch input")

# --- Brewing System Init ---
model = BrewingModel()
gui = BrewingGUI(model)
controller = BrewingController(model, gui)

# --- Splash Screen ---
show_splash_screen("S:/splash.bmp")  # Replace with actual image path

# --- Synchronous Main Control Loop ---
def main_loop():
    loop_count = 0
    last_temp_update = time.ticks_ms()
    
    while True:
        current_time = time.ticks_ms()
        
        # Update temperature every 500ms (not every loop for stability)
        if time.ticks_diff(current_time, last_temp_update) >= 500:
            model.update_temperature()
            last_temp_update = current_time
        
        # Get PID output
        pid_output = model.get_heater_output()

        # Hardware control with safety checks
        if (model.heater_enabled and 
            model.heating_on and 
            pid_output > 0 and 
            0.0 <= model.temperature <= 100.0):  # Safety check
            heater_on(pid_output)
        else:
            heater_off()

        # Update GUI every loop (LVGL handles its own timing)
        gui.update(
            temp=model.temperature,
            setpoint=model.setpoint,
            heater=pid_output,
            pump=model.pump_on,
            stage=model.stage
        )

        # Process LVGL tasks (handles touch events automatically)
        lv.task_handler()
        
        # Debug output every 50 loops (~5 seconds)
        loop_count += 1
        if loop_count % 50 == 0:
            print(f"🌡️ Temp: {model.temperature:.1f}°C, Target: {model.setpoint:.1f}°C, Heater: {pid_output:.1f}%")

        # Small delay to prevent overwhelming the system
        time.sleep_ms(100)

# --- Asynchronous Main Loop (Recommended) ---
async def async_main_loop():
    """
    Non-blocking async main loop - allows concurrent tasks
    This is the recommended approach for better responsiveness
    """
    loop_count = 0
    last_temp_update = time.ticks_ms()
    last_debug_output = time.ticks_ms()
    
    print("🚀 Starting async main loop...")
    
    while True:
        current_time = time.ticks_ms()
        
        # Update temperature every 500ms for stability
        if time.ticks_diff(current_time, last_temp_update) >= 500:
            model.update_temperature()
            last_temp_update = current_time
        
        # Get PID output
        pid_output = model.get_heater_output()

        # Hardware control with enhanced safety checks
        if (model.heater_enabled and 
            model.heating_on and 
            pid_output > 0 and 
            0.0 <= model.temperature <= 100.0):  # Temperature range check
            heater_on(pid_output)
        else:
            heater_off()

        # Update GUI (LVGL handles its own timing)
        gui.update(
            temp=model.temperature,
            setpoint=model.setpoint,
            heater=pid_output,
            pump=model.pump_on,
            stage=model.stage
        )

        # Process LVGL tasks (handles touch events automatically)
        lv.task_handler()
        
        # Debug output every 5 seconds instead of every N loops
        if time.ticks_diff(current_time, last_debug_output) >= 5000:
            print(f"🌡️ Temp: {model.temperature:.1f}°C, Target: {model.setpoint:.1f}°C, "
                  f"Heater: {pid_output:.1f}%, Stage: {model.stage}")
            
            if touch_driver and touch_driver.is_pressed():
                x, y = touch_driver.get_coordinates()
                print(f"👆 Touch active at ({x}, {y})")
            
            last_debug_output = current_time

        # Async sleep allows other coroutines to run
        await asyncio.sleep_ms(100)

# --- Additional Async Tasks ---
async def wifi_monitor():
    """Monitor Wi-Fi connection and attempt reconnection"""
    import network
    
    while True:
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            print("📶 Wi-Fi disconnected, attempting reconnection...")
            connect_wifi(SSID, PASSWORD)
        
        await asyncio.sleep(30)  # Check every 30 seconds

async def temperature_logger():
    """Log temperature data periodically"""
    log_file = "temp_log.txt"
    
    while True:
        try:
            timestamp = time.localtime()
            log_entry = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}," \
                       f"{model.temperature:.2f},{model.setpoint:.2f}," \
                       f"{model.get_heater_output():.1f},{model.pump_on}\n"
            
            with open(log_file, "a") as f:
                f.write(log_entry)
                
        except Exception as e:
            print(f"📝 Logging error: {e}")
        
        await asyncio.sleep(60)  # Log every minute

async def safety_monitor():
    """Enhanced safety monitoring task"""
    fault_count = 0
    max_faults = 3
    
    while True:
        try:
            # Check for sensor faults
            if not (0.0 <= model.temperature <= 100.0):
                fault_count += 1
                print(f"⚠️ Temperature fault #{fault_count}: {model.temperature:.2f}°C")
                
                if fault_count >= max_faults:
                    print("🚨 EMERGENCY SHUTDOWN - Multiple sensor faults detected")
                    model.heater_enabled = False
                    model.heating_on = False
                    model.stage = "FAULT"
                    heater_off()
                    # Continue monitoring but keep heater off
            else:
                # Reset fault counter on good reading
                if fault_count > 0:
                    fault_count = max(0, fault_count - 1)
            
            # Check for overheating
            if model.temperature > model.setpoint + 5.0 and model.heater_enabled:
                print(f"🔥 Overheating detected! {model.temperature:.1f}°C > {model.setpoint + 5.0:.1f}°C")
                model.heating_on = False
                heater_off()
            
        except Exception as e:
            print(f"🛡️ Safety monitor error: {e}")
        
        await asyncio.sleep(1)  # Check safety every second

async def brewing_automation():
    """Optional brewing automation sequences"""
    while True:
        # This could implement mash schedules, step programs, etc.
        # For now, just a placeholder
        
        if model.stage == "Auto_Mash":
            # Example: Automatic mashing sequence
            mash_temps = [52, 62, 72, 78]  # Step mash temperatures
            for temp in mash_temps:
                model.set_target_temperature(temp)
                print(f"🌾 Mash step: {temp}°C")
                
                # Wait for temperature to stabilize
                while abs(model.temperature - temp) > 1.0:
                    await asyncio.sleep(5)
                
                # Hold temperature for 20 minutes
                await asyncio.sleep(1200)  # 20 minutes
            
            model.stage = "Completed"
        
        await asyncio.sleep(10)

# --- Async Main Function ---
async def run_async_system():
    """Run the complete async brewing system"""
    print("🔄 Starting async brewing system...")
    
    # Create all async tasks
    tasks = [
        asyncio.create_task(async_main_loop()),
        asyncio.create_task(wifi_monitor()),
        asyncio.create_task(temperature_logger()),
        asyncio.create_task(safety_monitor()),
        asyncio.create_task(brewing_automation())
    ]
    
    try:
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n🛑 Async system shutdown requested")
        # Cancel all tasks
        for task in tasks:
            task.cancel()
    except Exception as e:
        print(f"💥 Async system error: {e}")
        # Emergency shutdown
        heater_off()
        if hasattr(model, 'pump_pin'):
            model.pump_pin.value(0)

# --- Startup Options ---
def choose_operation_mode():
    """Choose between sync and async operation"""
    # For now, default to async (you can add input later for selection)
    USE_ASYNC = True  # Set to False for synchronous operation
    
    if USE_ASYNC:
        print("⚡ Using async operation mode (recommended)")
        return "async"
    else:
        print("🔄 Using synchronous operation mode")
        return "sync"

# --- Error Handling Wrappers ---
def safe_sync_main():
    """Synchronous main function with error handling"""
    try:
        print("🚀 Starting synchronous brewing controller...")
        main_loop()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
    except Exception as e:
        print(f"💥 Critical error: {e}")
        # Emergency shutdown
        heater_off()
        if hasattr(model, 'pump_pin'):
            model.pump_pin.value(0)
    finally:
        print("🏁 Brewing controller stopped")

async def safe_async_main():
    """Asynchronous main function with error handling"""
    try:
        print("🚀 Starting asynchronous brewing controller...")
        await run_async_system()
    except KeyboardInterrupt:
        print("\n🛑 Async shutdown requested")
    except Exception as e:
        print(f"💥 Async critical error: {e}")
        # Emergency shutdown
        heater_off()
        if hasattr(model, 'pump_pin'):
            model.pump_pin.value(0)
    finally:
        print("🏁 Async brewing controller stopped")

# --- Debug and Testing Functions ---
def debug_touch():
    """Debug touch functionality"""
    if not touch_driver:
        print("❌ Touch driver not available")
        return
    
    print("🧪 Starting touch debug mode for 10 seconds...")
    start_time = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start_time) < 10000:
        if touch_driver.is_pressed():
            x, y = touch_driver.get_coordinates()
            print(f"📍 Touch: ({x:3d}, {y:3d})")
        time.sleep_ms(200)
    
    print("✅ Touch debug complete")

def startup_menu():
    """Simple startup menu for debugging and testing"""
    print("\n" + "="*50)
    print("🍺 Brewing Controller Startup Menu")
    print("="*50)
    print("1. Normal operation (async)")
    print("2. Normal operation (sync)")  
    print("3. Touch test mode")
    print("4. Touch debug")
    print("5. I2C device scan")
    print("6. Temperature sensor test")
    print("="*50)
    
    # For production, just use option 1 (async)
    # For debugging, you could add input() here
    choice = "1"  # Default to async operation
    
    return choice

async def test_temperature_sensor():
    """Test temperature sensor readings"""
    print("🌡️ Testing temperature sensor for 30 seconds...")
    start_time = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start_time) < 30000:
        model.update_temperature()
        print(f"Temperature: {model.temperature:.2f}°C")
        await asyncio.sleep(1)
    
    print("✅ Temperature sensor test complete")

# --- Main Startup Logic ---
def main():
    """Main startup function"""
    choice = startup_menu()
    
    if choice == "1":
        # Async operation (recommended)
        try:
            asyncio.run(safe_async_main())
        except Exception as e:
            print(f"Failed to start async mode: {e}")
            print("Falling back to sync mode...")
            safe_sync_main()
    
    elif choice == "2":
        # Synchronous operation
        safe_sync_main()
    
    elif choice == "3":
        # Touch test
        if touch_driver:
            print("🖐️ Touch test mode - touch screen (Ctrl+C to exit)")
            try:
                while True:
                    if touch_driver.is_pressed():
                        x, y = touch_driver.get_coordinates()
                        print(f"📍 Touch at ({x}, {y})")
                    time.sleep_ms(100)
            except KeyboardInterrupt:
                print("\n✅ Touch test ended")
        else:
            print("❌ Touch driver not available")
    
    elif choice == "4":
        # Touch debug
        debug_touch()
    
    elif choice == "5":
        # I2C scan
        scan_i2c()
    
    elif choice == "6":
        # Temperature sensor test
        try:
            asyncio.run(test_temperature_sensor())
        except:
            # Fallback to sync version
            print("🌡️ Testing temperature sensor (sync mode)...")
            for i in range(30):
                model.update_temperature()
                print(f"Temperature: {model.temperature:.2f}°C")
                time.sleep(1)
    
    else:
        print("Invalid choice, starting async operation...")
        try:
            asyncio.run(safe_async_main())
        except Exception as e:
            print(f"Failed to start async mode: {e}")
            safe_sync_main()

# --- Start the system ---
if __name__ == "__main__":
    main()
else:
    # If imported as module, default to async
    try:
        asyncio.run(safe_async_main())
    except:
        safe_sync_main()