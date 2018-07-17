# 开源个人博客, 一行指令，运行自己的专属博客

博文支持markdown格式的上传和编辑。支持全文搜索。

### 通过环境变量来指定相关配置信息
- AUTHOR： 这个博客的所有者， eg: 夏洛之枫(默认)。博客名就会变成 夏洛之枫的个人博客，默认导入的博文作者也会是 夏洛之枫
- USERNAME: 登陆用户名。eg: test(默认)。个人博客只支持单用户登录以对博文进行上传，修改和删除。
- PASSWORD: 登陆密码。eg: 12345(默认)。

其它配置信息参见[settings.py](https://github.com/ShichaoMa/blog/edit/master/settings.py)
# START
```
# 自行安装python3.6+
git clone https://github.com/ShichaoMa/blog.git
cd blog
pip install -e .
uvicorn blog.web_app:app --log-level debug

```

### 首页
![](https://github.com/ShichaoMa/blog/blob/master/1.jpg)
### 文章正文
![](https://github.com/ShichaoMa/blog/blob/master/2.jpg)
### 全部文章
![](https://github.com/ShichaoMa/blog/blob/master/3.jpg)
### 登录
![](https://github.com/ShichaoMa/blog/blob/master/4.jpg)
### 上传文章
![](https://github.com/ShichaoMa/blog/blob/master/5.jpg)
### 个人介绍
![](https://github.com/ShichaoMa/blog/blob/master/6.jpg)
### 联系方式
![](https://github.com/ShichaoMa/blog/blob/master/7.jpg)
### 修改文章
![](https://github.com/ShichaoMa/blog/blob/master/10.png)
![](https://github.com/ShichaoMa/blog/blob/master/8.png)
### 新增少量实时修改功能
![](https://github.com/ShichaoMa/blog/blob/master/9.png)