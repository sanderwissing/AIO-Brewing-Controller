# webserver.py

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
            except:
                pass

        # Build HTML response
        html = f"""<!DOCTYPE html>
        <html>
        <head><title>Brewing PID Control</title></head>
        <body>
        <h2>Current Temp: {model.temperature:.2f}°C</h2>
        <form>
            P: <input name="p" value="{model.pid.kp}"><br>
            I: <input name="i" value="{model.pid.ki}"><br>
            D: <input name="d" value="{model.pid.kd}"><br>
            <input type="submit" value="Update PID">
        </form>
        </body>
        </html>"""

        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(html)
        cl.close()
