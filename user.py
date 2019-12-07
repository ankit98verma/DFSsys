from cmd_handle import *
from data_handle import *
from queue_packet_handle import *
from threads_handle import *


class User:

    def __init__(self, path="user.config"):
        # initialize the protocol and operation related variable
        print("Welcome!")

        self.data = DFSsysDataHandle(path=path)
        self.queue_packet_handle = DFSsysQueuePacketHandle(self.data)
        self.cmd_handle = DFSsysCmdHandle(self.data)
        self.thread_handle = DFSsysThreadHandle(self.data)


if __name__ == '__main__':
    u = User()
    u.cmd_handle.handle_input()
