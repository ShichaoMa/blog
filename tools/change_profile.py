#!/root/.pyenv/shims/python
# -*- coding:utf-8 -*-
import re
import os
import sys

conf = open("/etc/nginx/conf.d/blog.conf", "r")

data = conf.read()

data = re.sub("(uwsgi_pass )(.*?)(:3031;)", "\g<1>%s\g<3>"%sys.argv[1], data)

conf.close()

conf = open("/etc/nginx/conf.d/blog.conf", "w")

conf.write(data)

conf.close()

reboot = open("/etc/remote_reboot.py", "r")

data = reboot.read()

data = re.sub("(--host )(.*)( --port 22)", "\g<1>%s\g<3>"%sys.argv[1], data)

reboot.close()

reboot = open("/etc/remote_reboot.py", "w")

reboot.write(data)

reboot.close()

os.system("systemctl restart nginx")
