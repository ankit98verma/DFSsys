from cmd_handle import *
from data_handle import *
from queue_packet_handle import *
from threads_handle import *


if __name__ == '__main__':
    path = "user.config"
    data = DFSsysDataHandle(path=path)
    queue_packet_handle = DFSsysQueuePacketHandle(data)
    cmd_handle = DFSsysCmdHandle(data)
    thread_handle = DFSsysThreadHandle(data)
    cmd_handle.handle_input()
