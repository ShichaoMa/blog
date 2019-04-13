import os
import re
import time

regex = re.compile("(modified:)|(Untracked files)")


def main():
    for path in ("/root/blog", "/home/learn/deep-learning"):
        os.chdir(path)
        process = os.popen("/usr/bin/git status")
        buffer = process.read()
        if regex.search(buffer):
            os.system("/usr/bin/git add .")
            os.system("/usr/bin/git commit -m 'Save: Data auto save'")
            os.system("/usr/bin/git push")


if __name__ == "__main__":
    while True:
        time.sleep(10)
        main()
