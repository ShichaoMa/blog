# 开源个人博客, 一行指令，运行自己的专属博客

博文支持markdown格式的上传和编辑。支持全文搜索。

### 通过环境变量来指定相关配置信息
- AUTHOR： 这个博客的所有者， eg: 夏洛之枫(默认)。博客名就会变成__夏洛之枫的个人博客__，默认导入的博文作者也会是__夏洛之枫__
- DB: 使用的数据库，eg: ES or SQLITE(默认)。早期版本使用的数据存储是elasticsearch, 但是由于我需要将网站部署到树莓派上，而树莓派配置较低，无法很好的运行es, 于是我在保持es实现的基础上，追加实现了使用sqlite作为数据存储的的方案。使用es作为数据库支持全部字段检索，sqllite仅支持正文。
- USERNAME: 登陆用户名。eg: test(默认)。个人博客只支持单用户登录以对博文进行上传，修改和删除。
- PASSWORD: 登陆密码。eg: 12345(默认)。
- THREADED: 是否启用多线程server。eg: False(默认)。
- PROCESSES: server进程数。eg: 1(默认)。

其它配置信息参见[settings.py](https://github.com/ShichaoMa/blog/edit/master/settings.py)
# START
### 推荐使用docker来运行，非常简单，只需要一行代码，docker安装方法在我的[blog](http://www.mashichao.com:5678)里面可以找到。
```
sudo docker run -e "HOST=0.0.0.0" -e "DB=SQLITE" -e "AUTHOR=你的名字" -e "USERNAME=xxxxx" -e "PASSWORD=xxxxxx" -v /home/cn/db:/app/db -p 5000:5000 cnaafhvk/blog:latest python3.6 start.py
```
### 或者常规方案
```
# 自行安装python3
git clone https://github.com/ShichaoMa/blog.git
cd blog
pip install -r docker/requirements.txt
# 自行设置配置变量
python start.py
```
### 首页
![](https://github.com/ShichaoMa/blog/blob/master/1.jpg)
### 文章正文
![](https://github.com/ShichaoMa/blog/blob/master/2.jpg)
### 全部文章
![](https://github.com/ShichaoMa/blog/blob/master/3.jpg)
### 登陆
![](https://github.com/ShichaoMa/blog/blob/master/4.jpg)
### 上传文章
![](https://github.com/ShichaoMa/blog/blob/master/5.jpg)
### 个人介绍
![](https://github.com/ShichaoMa/blog/blob/master/6.jpg)
### 联系方式
![](https://github.com/ShichaoMa/blog/blob/master/7.jpg)
### 修改文章
![](https://github.com/ShichaoMa/blog/blob/master/8.jpg)