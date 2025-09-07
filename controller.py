from machine import Timer

class BrewingController:
    def __init__(self, model, gui):
        self.model = model
        self.gui = gui
        self.timer = Timer(-1)
        self.timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: self.loop())

    def loop(self):
        self.model.update_temperature()
        heater_output = self.model.get_heater_output()
        self.gui.update(
            temp=self.model.temperature,
            setpoint=self.model.setpoint,
            heater=heater_output,
            pump=self.model.pump_on,
            stage=self.model.stage
        )