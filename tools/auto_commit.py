#!/usr/bin/env python3
import os
import re
import time

from argparse import ArgumentParser
regex = re.compile("(modified:)|(Untracked files)")


def main(paths):
    for path in paths:
        os.chdir(path)
        process = os.popen("/usr/bin/git status")
        buffer = process.read()
        if regex.search(buffer):
            os.system("/usr/bin/git add .")
            os.system("/usr/bin/git commit -m 'Save: Data auto save'")
            os.system("/usr/bin/git push")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("path", nargs="+", help="Which path to run save check. ")
    parser.add_argument("-i", "--interval", type=int, help="Check interval. ")
    args = parser.parse_args()
    while True:
        time.sleep(args.interval)
        print("Save check")
        main(args.path)
