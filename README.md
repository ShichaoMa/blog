# blog
请使用docker安装
```
docker run -p 9200:9200 -v /home/ubuntu/data:/home/ubuntu/data -v /home/ubuntu/logs:/home/ubuntu/logs -v /home/ubuntu/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml -e "http.host=0.0.0.0" -e "transport.host=127.0.0.1" docker.elastic.co/elasticsearch/elasticsearch:5.3.3
curl -XPUT localhost:9200/blog -u "elastic:changeme" -d '
{
  "mappings": {
    "artiles": {
      "properties": {
        "id": {
          "type": "keyword"
        },
        "tags": {
          "type": "text"
        },
        "description": {
          "type": "text"
        },
        "title": {
          "type": "text"
        },
        "author": {
          "type": "text"
        },
        "created_at": {
          "type": "date"
        },
        "updated_at": {
          "type": "date"
        },
        "feature": {
          "type": "boolean"
        }
      }
    }
  }
}'
docker run -e "HOST=0.0.0.0" -e "ES_HOST=192.168.21.58" -v/home/ubuntu/articles:/app/articles -p 5000:5000 cnaafhvk/blog:latest python3.6 start.py
```
![](https://github.com/ShichaoMa/blog/blob/master/demo1.jpg)
![](https://github.com/ShichaoMa/blog/blob/master/demo2.jpg)
![](https://github.com/ShichaoMa/blog/blob/master/demo3.jpg)
![](https://github.com/ShichaoMa/blog/blob/master/demo4.jpg)