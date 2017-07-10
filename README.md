# blog
请使用docker来运行
```
sudo docker run -e "HOST=0.0.0.0" -e "DB=SQLITE" -e "AUTHOR=你的名字" -e "USERNAME=xxxxx" -e "PASSWORD=xxxxxx" -v /home/cn/db:/app/db -p 5000:5000 cnaafhvk/blog:latest python3.6 start.py
```
![](https://github.com/ShichaoMa/blog/blob/master/1.jpg)
![](https://github.com/ShichaoMa/blog/blob/master/2.jpg)
![](https://github.com/ShichaoMa/blog/blob/master/3.jpg)