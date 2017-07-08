# -*- coding:utf-8 -*-
import os
import sys

os.system("rm -rf wand")
os.system("cp -r ../templetes ./templetes")
os.system("cp -r ../static ./static")
os.system("cp ../start.py start.py")
os.system("cp ../settings.py settings.py")
os.system("docker build -f blog -t cnaafhvk/blog:latest .")
os.system("docker push cnaafhvk/blog")