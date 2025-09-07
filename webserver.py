import socket

def start_web_server(model):
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Web server listening on port 80...')

    while True:
        cl, addr = s.accept()
        request = cl.recv(1024).decode()

        # Parse GET parameters
        if 'GET /?' in request:
            try:
                params = request.split(' ')[1].split('?')[1].split('&')
                for param in params:
                    key, val = param.split('=')
                    if key == 'p': model.pid.kp = float(val)
                    if key == 'i': model.pid.ki = float(val)
                    if key == 'd': model.pid.kd = float(val)
                    if key == 'pump': model.toggle_pump()
                    if key == 'heater': model.toggle_heater_enabled()  # 👈 Updated call
            except:
                pass

        # Build HTML response
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>Brewing PID Control</title>
            <style>
                body {{ font-family: Arial; background: #f4f4f4; padding: 20px; }}
                h2 {{ color: #333; }}
                .status {{ margin-top: 10px; font-weight: bold; }}
                button {{ padding: 10px 20px; margin: 5px; }}
            </style>
        </head>
        <body>
            <h2>Current Temperature: {model.temperature:.2f}°C</h2>
            <div class="status">
                Heater Enabled: {'YES' if model.heater_enabled else 'NO'}<br>
                Pump: {'ON' if model.pump_on else 'OFF'}
            </div>
            <form>
                <h3>PID Settings</h3>
                P: <input name="p" value="{model.pid.kp}"><br>
                I: <input name="i" value="{model.pid.ki}"><br>
                D: <input name="d" value="{model.pid.kd}"><br>
                <input type="submit" value="Update PID">
            </form>
            <form>
                <h3>Actuator Control</h3>
                <button name="pump" value="toggle">Toggle Pump</button>
                <button name="heater" value="toggle">Toggle Heater Enabled</button>
            </form>
        </body>
        </html>"""

        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(html)
        cl.close()
