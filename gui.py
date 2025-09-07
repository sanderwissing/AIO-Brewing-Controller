import lvgl as lv
import network
import time

class BrewingGUI:
    def __init__(self, model):
        self.model = model
        self.create_flashing_style()
        self.build_ui()
        lv.timer.create(lambda t: self.update_wifi_icon(), 5000, None)

    def create_flashing_style(self):
        self.flash_style = lv.style_t()
        self.flash_style.init()
        self.flash_style.set_text_color(lv.color_hex(0xFF0000))  # Red

    def build_ui(self):
        self.scr = lv.obj()

        self.temp_label = lv.label(self.scr)
        self.temp_label.set_text("Temp: --°C")
        self.temp_label.align(lv.ALIGN.TOP_MID, 0, 10)

        self.setpoint_label = lv.label(self.scr)
        self.setpoint_label.set_text("Setpoint: --°C")
        self.setpoint_label.align(lv.ALIGN.TOP_MID, 0, 40)

        self.wifi_icon = lv.label(self.scr)
        self.wifi_icon.set_text("📶")
        self.wifi_icon.align(lv.ALIGN.TOP_RIGHT, -10, 10)

        self.heater_bar = lv.bar(self.scr)
        self.heater_bar.set_size(200, 20)
        self.heater_bar.align(lv.ALIGN.BOTTOM_MID, 0, -30)
        self.heater_bar.set_range(0, 100)
        self.heater_bar.set_value(0, lv.ANIM.OFF)

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

        lv.scr_load(self.scr)

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
        self.temp_label.set_text(f"Temp: {temp:.1f}°C")
        self.setpoint_label.set_text(f"Setpoint: {setpoint:.1f}°C")
        self.heater_bar.set_value(int(heater), lv.ANIM.OFF)
        self.update_heater_visual()

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

        rssi = wlan.status('rssi')
        if rssi >= -50:
            self.wifi_icon.set_text("📶📶📶📶")
        elif rssi >= -60:
            self.wifi_icon.set_text("📶📶📶")
        elif rssi >= -70:
            self.wifi_icon.set_text("📶📶")
        else:
            self.wifi_icon.set_text("📶")

# --- Splash Screen ---
def show_splash_screen(image_path):
    splash = lv.obj()
    splash.set_size(480, 480)
    splash.center()

    img = lv.img(splash)
    img.set_src(image_path)
    img.center()

    time.sleep(3)
    splash.delete()

# --- GUI Update Hook ---
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