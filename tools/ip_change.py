#!/home/pi/.pyenv/shims/python
# -*- coding:utf-8 -*-
import sys
import time
import socket
import requests
import paramiko

current_ip = None
user = "root"
password = sys.argv[2]
port = 28553
host = sys.argv[1]


def change(ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, user, password)
    stdin, stdout, stderr = ssh.exec_command("./change_profile.py %s"%ip)
    error = stderr.read()
    out = stdout.read()
    print(error, out)
    ssh.close()
    return error == b""


def getip():
    # sock = socket.create_connection(('ns1.dnspod.net', 6666))
    # ip = sock.recv(16)
    # sock.close()
    # return ip.decode("utf-8")
    return requests.get("http://ip.42.pl/raw").text

if __name__ == '__main__':
    while True:
        try:
            ip = getip()
            print(ip)
            if current_ip != ip:
                if change(ip):
                    current_ip = ip
        except Exception as e:
            print(e)
        time.sleep(30)
        sys.stdout.flush()
