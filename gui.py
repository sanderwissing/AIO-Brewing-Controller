import lvgl as lv
import network
import time

class BrewingGUI:
    def __init__(self, model):
        self.model = model
        self.create_flashing_style()
        self.build_ui()
        lv.timer.create(lambda t: self.update_wifi_icon(), 5000, None)
        lv.timer.create(lambda t: self.update_ip_address(), 10000, None)  # Update IP every 10 seconds

    def create_flashing_style(self):
        self.flash_style = lv.style_t()
        self.flash_style.init()
        self.flash_style.set_text_color(lv.color_hex(0xFF0000))  # Red

    def build_ui(self):
        self.scr = lv.obj()

        self.temp_label = lv.label(self.scr)
        self.temp_label.set_text("Temp: --°C")
        self.temp_label.align(lv.ALIGN.TOP_MID, 0, 10)
        # Set bigger font for temperature label
        big_font_style = lv.style_t()
        big_font_style.init()
        # Use a built-in large font or custom font if available
        # Example: lv.font_montserrat_48 (if available)
        if hasattr(lv, 'font_montserrat_48'):
            big_font_style.set_text_font(lv.font_montserrat_48)
        else:
            big_font_style.set_text_font(lv.font_default())
        self.temp_label.add_style(big_font_style, 0)

        self.setpoint_label = lv.label(self.scr)
        self.setpoint_label.set_text("Setpoint: --°C")
        self.setpoint_label.align(lv.ALIGN.TOP_MID, 0, 40)

        self.wifi_icon = lv.label(self.scr)
        self.wifi_icon.set_text("📶")
        self.wifi_icon.align(lv.ALIGN.TOP_RIGHT, -10, 10)

        self.heater_bar = lv.bar(self.scr)
        self.heater_bar.set_size(200, 20)
        self.heater_bar.align(lv.ALIGN.BOTTOM_MID, 0, -60)  # Moved up to make room for IP
        self.heater_bar.set_range(0, 100)
        self.heater_bar.set_value(0, lv.ANIM.OFF)

        # Heater bar label
        self.heater_label = lv.label(self.scr)
        self.heater_label.set_text("Heater: 0%")
        self.heater_label.align(lv.ALIGN.BOTTOM_MID, 0, -80)

        self.btn_up = lv.btn(self.scr)
        self.btn_up.set_size(60, 40)
        self.btn_up.align(lv.ALIGN.TOP_LEFT, 10, 80)
        lv.label(self.btn_up).set_text("▲")
        self.btn_up.add_event_cb(lambda e: self.model.set_target_temperature(self.model.setpoint + 1), lv.EVENT.CLICKED, None)

        self.btn_down = lv.btn(self.scr)
        self.btn_down.set_size(60, 40)
        self.btn_down.align(lv.ALIGN.TOP_LEFT, 80, 80)
        lv.label(self.btn_down).set_text("▼")
        self.btn_down.add_event_cb(lambda e: self.model.set_target_temperature(self.model.setpoint - 1), lv.EVENT.CLICKED, None)

        self.btn_pump = lv.btn(self.scr)
        self.btn_pump.set_size(100, 40)
        self.btn_pump.align(lv.ALIGN.TOP_RIGHT, -10, 80)
        lv.label(self.btn_pump).set_text("Pump")
        self.btn_pump.add_event_cb(lambda e: self.model.toggle_pump(), lv.EVENT.CLICKED, None)

        self.btn_heat = lv.btn(self.scr)
        self.btn_heat.set_size(100, 40)
        self.btn_heat.align(lv.ALIGN.TOP_RIGHT, -10, 130)
        lv.label(self.btn_heat).set_text("Heater")
        self.btn_heat.add_event_cb(self.toggle_heater_ui, lv.EVENT.CLICKED, None)

        # Stage/Status label
        self.stage_label = lv.label(self.scr)
        self.stage_label.set_text("Stage: Idle")
        self.stage_label.align(lv.ALIGN.CENTER, 0, 50)

        # IP Address label - bottom of screen, smaller text
        self.ip_label = lv.label(self.scr)
        self.ip_label.set_text("IP: Connecting...")
        self.ip_label.align(lv.ALIGN.BOTTOM_MID, 0, -10)
        
        # Create smaller font style for IP address
        self.ip_style = lv.style_t()
        self.ip_style.init()
        self.ip_style.set_text_font(lv.font_default())  # Use default font but we'll make it smaller visually
        self.ip_style.set_text_color(lv.color_hex(0x808080))  # Gray color
        self.ip_label.add_style(self.ip_style, 0)

        # Settings button
        self.btn_settings = lv.btn(self.scr)
        self.btn_settings.set_size(60, 40)
        self.btn_settings.align(lv.ALIGN.TOP_RIGHT, -10, 180)
        lv.label(self.btn_settings).set_text("⚙️")
        self.btn_settings.add_event_cb(self.open_settings_dialog, lv.EVENT.CLICKED, None)
        self.net_status = lv.label(self.scr)
        self.net_status.set_text("●")
        self.net_status.align(lv.ALIGN.BOTTOM_MID, -80, -10)
        
        self.net_status_style = lv.style_t()
        self.net_status_style.init()
        self.net_status_style.set_text_color(lv.color_hex(0xFF0000))  # Red by default
        self.net_status.add_style(self.net_status_style, 0)

        lv.scr_load(self.scr)
        
        # Initial IP update
        self.update_ip_address()

    def get_ip_address(self):
        """Get current IP address"""
        try:
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                ip_info = wlan.ifconfig()
                return ip_info[0]  # IP address is first element
            else:
                return "Not Connected"
        except Exception as e:
            print(f"⚠️ Error getting IP: {e}")
            return "Error"

    def update_ip_address(self):
        """Update IP address display"""
        ip_addr = self.get_ip_address()
        
        if ip_addr == "Not Connected":
            self.ip_label.set_text("IP: Not Connected")
            # Set network status to red
            self.net_status_style.set_text_color(lv.color_hex(0xFF0000))  # Red
        elif ip_addr == "Error":
            self.ip_label.set_text("IP: Error")
            # Set network status to orange
            self.net_status_style.set_text_color(lv.color_hex(0xFFA500))  # Orange
        else:
            # Truncate IP if too long for display
            if len(ip_addr) > 15:
                display_ip = ip_addr[:12] + "..."
            else:
                display_ip = ip_addr
            
            self.ip_label.set_text(f"IP: {display_ip}")
            # Set network status to green
            self.net_status_style.set_text_color(lv.color_hex(0x00FF00))  # Green

    def toggle_heater_ui(self, event):
        self.model.toggle_heater_enabled()
        self.update_heater_visual()

    def update_heater_visual(self):
        if self.model.heater_enabled:
            self.heater_bar.set_style_bg_color(lv.color_hex(0xFF0000), 0)  # Red
        else:
            self.heater_bar.set_style_bg_color(lv.color_hex(0x808080), 0)  # Gray

    def start_temp_flash(self):
        def flash_cb(timer):
            current_opacity = self.temp_label.get_style_text_opa(0)
            new_opacity = lv.OPA.TRANSP if current_opacity == lv.OPA.COVER else lv.OPA.COVER
            self.temp_label.set_style_text_opa(new_opacity, 0)

        self.temp_flash_timer = lv.timer.create(flash_cb, 500, None)

    def stop_temp_flash(self):
        if hasattr(self, "temp_flash_timer"):
            self.temp_flash_timer.pause()
            self.temp_label.set_style_text_opa(lv.OPA.COVER, 0)

    def update(self, temp, setpoint, heater, pump, stage):
        # Update temperature display
        self.temp_label.set_text(f"Temp: {temp:.1f}°C")
        self.setpoint_label.set_text(f"Setpoint: {setpoint:.1f}°C")
        
        # Update heater bar and label
        self.heater_bar.set_value(int(heater), lv.ANIM.OFF)
        self.heater_label.set_text(f"Heater: {heater:.1f}%")
        self.update_heater_visual()

        # Update stage
        self.stage_label.set_text(f"Stage: {stage}")

        # Update pump button appearance
        pump_btn_label = self.btn_pump.get_child(0)
        if pump:
            pump_btn_label.set_text("Pump ON")
            self.btn_pump.set_style_bg_color(lv.color_hex(0x0080FF), 0)  # Blue when on
        else:
            pump_btn_label.set_text("Pump OFF")
            self.btn_pump.set_style_bg_color(lv.color_hex(0x606060), 0)  # Gray when off

        # Update heater button appearance
        heat_btn_label = self.btn_heat.get_child(0)
        if self.model.heater_enabled:
            if self.model.heating_on and heater > 0:
                heat_btn_label.set_text("Heat ON")
                self.btn_heat.set_style_bg_color(lv.color_hex(0xFF4000), 0)  # Red-orange when heating
            else:
                heat_btn_label.set_text("Heat RDY")
                self.btn_heat.set_style_bg_color(lv.color_hex(0xFF8000), 0)  # Orange when ready
        else:
            heat_btn_label.set_text("Heat OFF")
            self.btn_heat.set_style_bg_color(lv.color_hex(0x606060), 0)  # Gray when disabled

        # Temperature sensor error handling
        if 0.0 <= temp <= 100.0:
            self.temp_label.remove_style_all()
            self.stop_temp_flash()
        else:
            self.temp_label.add_style(self.flash_style, 0)
            self.start_temp_flash()

    def update_wifi_icon(self):
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            self.wifi_icon.set_text("❌")
            return

        try:
            rssi = wlan.status('rssi')
            if rssi >= -50:
                self.wifi_icon.set_text("📶📶📶📶")
            elif rssi >= -60:
                self.wifi_icon.set_text("📶📶📶")
            elif rssi >= -70:
                self.wifi_icon.set_text("📶📶")
            else:
                self.wifi_icon.set_text("📶")
        except:
            self.wifi_icon.set_text("📶")

    def show_error_screen(self):
        """Display error/fault screen"""
        # Clear current screen
        self.scr.clean()
        
        # Create error display
        error_title = lv.label(self.scr)
        error_title.set_text("⚠️ SYSTEM FAULT ⚠️")
        error_title.align(lv.ALIGN.CENTER, 0, -50)
        
        error_style = lv.style_t()
        error_style.init()
        error_style.set_text_color(lv.color_hex(0xFF0000))
        error_title.add_style(error_style, 0)
        
        error_msg = lv.label(self.scr)
        error_msg.set_text("Temperature sensor fault\nHeating disabled for safety\nCheck sensor connections")
        error_msg.align(lv.ALIGN.CENTER, 0, 0)
        
        # Keep IP display even in error mode
        self.ip_label = lv.label(self.scr)
        self.ip_label.align(lv.ALIGN.BOTTOM_MID, 0, -10)
        self.ip_label.add_style(self.ip_style, 0)
        
        self.net_status = lv.label(self.scr)
        self.net_status.set_text("●")
        self.net_status.align(lv.ALIGN.BOTTOM_MID, -80, -10)
        self.net_status.add_style(self.net_status_style, 0)
        
        self.update_ip_address()

    def get_network_info(self):
        """Get detailed network information for debugging"""
        try:
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                config = wlan.ifconfig()
                return {
                    'ip': config[0],
                    'subnet': config[1],
                    'gateway': config[2],
                    'dns': config[3],
                    'mac': ':'.join(['%02x' % b for b in wlan.config('mac')]),
                    'rssi': wlan.status('rssi')
                }
            else:
                return {'status': 'disconnected'}
        except Exception as e:
            return {'error': str(e)}

    def open_settings_dialog(self, event):
        # Create a modal dialog
        self.settings_dialog = lv.obj(self.scr)
        self.settings_dialog.set_size(300, 200)
        self.settings_dialog.align(lv.ALIGN.CENTER, 0, 0)
        self.settings_dialog.set_style_bg_color(lv.color_hex(0xFFFFFF), 0)
        self.settings_dialog.set_style_radius(10, 0)

        title = lv.label(self.settings_dialog)
        title.set_text("Settings")
        title.align(lv.ALIGN.TOP_MID, 0, 10)

        # Auto-Tune button
        btn_autotune = lv.btn(self.settings_dialog)
        btn_autotune.set_size(180, 40)
        btn_autotune.align(lv.ALIGN.CENTER, 0, 30)
        lv.label(btn_autotune).set_text("Auto-Tune PID")
        btn_autotune.add_event_cb(self.run_autotune, lv.EVENT.CLICKED, None)

        # Calibration offset input
        offset_label = lv.label(self.settings_dialog)
        offset_label.set_text("Calibration Offset:")
        offset_label.align(lv.ALIGN.CENTER, 0, 80)

        self.offset_input = lv.textarea(self.settings_dialog)
        self.offset_input.set_size(100, 30)
        self.offset_input.align(lv.ALIGN.CENTER, 80, 80)
        self.offset_input.set_text(str(getattr(self.model.sensor, 'calibration_offset', 0.0)))

        btn_set_offset = lv.btn(self.settings_dialog)
        btn_set_offset.set_size(80, 30)
        btn_set_offset.align(lv.ALIGN.CENTER, 0, 120)
        lv.label(btn_set_offset).set_text("Set Offset")
        btn_set_offset.add_event_cb(self.set_calibration_offset, lv.EVENT.CLICKED, None)

        # Close button
        btn_close = lv.btn(self.settings_dialog)
        btn_close.set_size(80, 30)
        btn_close.align(lv.ALIGN.BOTTOM_MID, 0, -10)
        lv.label(btn_close).set_text("Close")
        btn_close.add_event_cb(lambda e: self.settings_dialog.delete(), lv.EVENT.CLICKED, None)

    def set_calibration_offset(self, event):
        try:
            offset = float(self.offset_input.get_text())
            if hasattr(self.model, 'set_calibration_offset'):
                self.model.set_calibration_offset(offset)
            msg = lv.label(self.settings_dialog)
            msg.set_text(f"Offset set to {offset}")
            msg.align(lv.ALIGN.CENTER, 0, 150)
        except Exception as e:
            msg = lv.label(self.settings_dialog)
            msg.set_text(f"Error: {e}")
            msg.align(lv.ALIGN.CENTER, 0, 150)

# --- Splash Screen ---
def show_splash_screen(image_path):
    splash = lv.obj()
    splash.set_size(480, 480)
    splash.center()

    # Title
    title = lv.label(splash)
    title.set_text("🍺 Brewing Controller")
    title.align(lv.ALIGN.TOP_MID, 0, 50)
    
    title_style = lv.style_t()
    title_style.init()
    title_style.set_text_color(lv.color_hex(0xFFFFFF))
    title.add_style(title_style, 0)

    # Try to load image, fallback to text if not available
    try:
        img = lv.img(splash)
        img.set_src(image_path)
        img.align(lv.ALIGN.CENTER, 0, 0)
    except:
        # Fallback to text logo if image not available
        logo = lv.label(splash)
        logo.set_text("🌡️\n⚡\n💧")
        logo.align(lv.ALIGN.CENTER, 0, 0)

    # Version info
    version = lv.label(splash)
    version.set_text("v1.0 - Touch Enabled")
    version.align(lv.ALIGN.BOTTOM_MID, 0, -30)

    lv.scr_load(splash)
    time.sleep(3)
    splash.delete()

# --- GUI Update Hook (Legacy compatibility) ---
def update_gui(current_temp, pid_output):
    scr = lv.scr_act()

    if hasattr(scr, "temp_label"):
        scr.temp_label.set_text(f"Temp: {current_temp:.1f}°C")

    if hasattr(scr, "heater_bar"):
        scr.heater_bar.set_value(int(pid_output * 100), lv.ANIM.ON)

    if hasattr(scr, "btn_heat") and hasattr(scr, "model"):
        if scr.model.heater_enabled:
            scr.heater_bar.set_style_bg_color(lv.color_hex(0xFF0000), 0)
        else:
            scr.heater_bar.set_style_bg_color(lv.color_hex(0x808080), 0)