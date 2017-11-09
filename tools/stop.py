#!/home/pi/.pyenv/shims/python
import os
import re

from argparse import ArgumentParser


def kill(pid, signal):
    try:
        os.kill(pid, signal)
    except ProcessLookupError:
        pass


def main(cmd, signal):
    current_pid = os.getpid()
    pids = list()
    ppids = list()
    buffer_lines = os.popen("ps -ef|grep '%s'"%cmd).readlines()
    for line in buffer_lines:
        if line.strip():
            ele = re.findall("(\S+)", line.strip())
            if int(ele[1]) != current_pid:
                pids.append(int(ele[1]))
                ppids.append(int(ele[2]))
    if len(pids) > 3:
        for index, pid in enumerate(pids):
            if pid in ppids:
                kill(pid, signal)
            elif ppids[index] in pids:
                kill(pid, signal)
    if len(pids) < 3:
        print("No such process")
    else:
        for pid in pids:
            kill(pid, signal)


if __name__ == "__main__":
    parse = ArgumentParser()
    parse.add_argument("-c", "--command", required=True, help="check command to stop. ")
    parse.add_argument("-s", "--signal", type=int, help="signal to send", default=15)
    args = parse.parse_args()
    main(args.command, args.signal)
