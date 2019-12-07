from DDS.cmd_handle import *
from DDS.data_handle import *
from DDS.queue_packet_handle import *
from DDS.threads_handle import *
import sys
import os


def main():
    path = "user.config"
    print("Name: ", sys.argv[0])
    root = str(os.getcwd())
    if len(sys.argv) == 1:
        print("Using following as root directory:\n%s\n" % os.getcwd(), end="")
    else:
        root = sys.argv[1]
    data = DFSsysDataHandle(path=path, root=root)
    queue_packet_handle = DFSsysQueuePacketHandle(data)
    cmd_handle = DFSsysCmdHandle(data)
    thread_handle = DFSsysThreadHandle(data)
    cmd_handle.handle_input()


if __name__ == '__main__':
    main()
