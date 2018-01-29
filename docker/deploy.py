# -*- coding:utf-8 -*-
import os
import sys

os.system("rm -rf templetes")
os.system("rm -rf static")
os.system("rm -rf blog")
os.system("cp -r ../templetes ./templetes")
os.system("cp -r ../static ./static")
os.system("cp ../start.py start.py")
os.system("cp ../blog.sql blog.sql")
os.system("cp ../blog.json blog.json")
os.system("cp -r ../blog blog")
os.system("cp ../settings.py settings.py")
os.system("sudo docker build -f blog.df -t cnaafhvk/blog:latest .")
os.system("sudo docker push cnaafhvk/blog")
