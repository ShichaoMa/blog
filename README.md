# 基于apistellar的个人博客

## Badge

### GitHub

[![GitHub followers](https://img.shields.io/github/followers/shichaoma.svg?label=github%20follow)](https://github.com/shichao.ma)
[![GitHub repo size in bytes](https://img.shields.io/github/repo-size/shichaoma/blog.svg)](https://github.com/shichaoma/blog)
[![GitHub stars](https://img.shields.io/github/stars/shichaoma/blog.svg?label=github%20stars)](https://github.com/shichaoma/blog)
[![GitHub release](https://img.shields.io/github/release/shichaoma/blog.svg)](https://github.com/shichaoma/blog/releases)
[![Github commits (since latest release)](https://img.shields.io/github/commits-since/shichaoma/blog/latest.svg)](https://github.com/shichaoma/blog)

[![Github All Releases](https://img.shields.io/github/downloads/shichaoma/blog/total.svg)](https://github.com/shichaoma/blog/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/shichaoma/blog.svg)](https://github.com/shichaoma/blog/releases)

博文支持markdown格式的上传和编辑，支持全文搜索。业务代码单元测试代码覆盖率100%。

通过环境变量来指定相关配置信息

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
![](https://github.com/ShichaoMa/blog/blob/master/resources/1.jpg)
### 文章正文
![](https://github.com/ShichaoMa/blog/blob/master/resources/2.jpg)
### 全部文章
![](https://github.com/ShichaoMa/blog/blob/master/resources/3.jpg)
### 登录
![](https://github.com/ShichaoMa/blog/blob/master/resources/4.jpg)
### 上传文章
![](https://github.com/ShichaoMa/blog/blob/master/resources/5.jpg)
### 个人介绍
![](https://github.com/ShichaoMa/blog/blob/master/resources/6.jpg)
### 联系方式
![](https://github.com/ShichaoMa/blog/blob/master/resources/7.jpg)
### 修改文章
![](https://github.com/ShichaoMa/blog/blob/master/resources/10.png)
![](https://github.com/ShichaoMa/blog/blob/master/resources/8.png)
### 新增少量实时修改功能
![](https://github.com/ShichaoMa/blog/blob/master/resources/9.png)