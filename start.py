# -*- coding:utf-8 -*-
import os

from blog import app


if __name__ == "__main__":
    app.run(debug=eval(os.environ.get("DEBUG", "False")),
            processes=int(os.environ.get("PROCESSES", 1)),
            threaded=eval(os.environ.get("THREADED", "False")),
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", 5000)))
