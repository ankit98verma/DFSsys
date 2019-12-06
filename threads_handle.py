import pickle as pk
import socket
import threading

from PyQt5.QtWidgets import *

from gui_handle import DFSsysGUIHandle
from packet import *


class DFSsysThreadHandle:

    def __init__(self, data):
        self.data = data
        self.start_threads()  # should be the last line in the __init__ function

    def start_threads(self):
        print("Starting the UDP thread")
        # thread for starting the UDP transmit
        th1 = threading.Thread(target=self.udp_transmit_thread, args=())
        self.data.threads.append(th1)

        # thread for starting the UDP receive
        th2 = threading.Thread(target=self.udp_receive_thread, args=())
        self.data.threads.append(th2)

        # thread for starting the regular checking of tables
        th3 = threading.Thread(target=self.onlines_manager, args=())
        self.data.threads.append(th3)

        # thread for GUI
        th4 = threading.Thread(target=self.setup_main_gui, args=())
        self.data.threads.append(th4)

        th5 = threading.Thread(target=self.online_packet_thread, args=())
        self.data.threads.append(th5)

        th6 = threading.Thread(target=self.process_packet_thread, args=())
        self.data.threads.append(th6)

        th7 = threading.Thread(target=self.requests_manager, args=())
        self.data.threads.append(th7)

        th8 = threading.Thread(target=self.tcp_listen_thread, args=())
        self.data.threads.append(th8)

        th9 = threading.Thread(target=self.tcp_transmit_thread, args=())
        self.data.threads.append(th9)

        # start all the data.threads
        th1.start()
        th2.start()
        th3.start()
        th4.start()
        th5.start()
        th6.start()
        th7.start()
        th8.start()
        th9.start()

    # UI related threads
    def setup_main_gui(self):
        app = QApplication([])
        self.data.UI = DFSsysGUIHandle(self.data.log_info, self.data.data_struct.onlines,
                                       self.data.data_struct.duplicate_packets, self.data.lock)

        # thread for starting the regular checking of tables
        th = threading.Thread(target=self.trigger_UI, args=())
        self.data.threads.append(th)
        th.start()

        self.data.UI.show_guis('-a')
        app.exec_()
        print('Exited UI\n', end="")

    def trigger_UI(self):
        while True:
            if self.data.close_event.is_set():
                break
            self.data.UI.trigger_guis('-a')
            time.sleep(self.data.basic_params['GUI_update_rate'] / 1000)
        print("Exiting trigger UI thread\n", end="")

    # database managers
    def requests_manager(self):
        while True:
            if self.data.close_event.is_set():
                break
            with self.data.lock:
                curr_time = int(round(time.time() * 1000))
                remove_list = []
                for k, v in self.data.requests_dict.items():
                    if (curr_time - v) > self.data.basic_params['Request_TOL']:
                        print("Removing the element %d" % k)
                        remove_list.append(k)
                for l in remove_list:
                    self.data.requests_dict.pop(l)
            time.sleep(self.data.basic_params['Requests_check_rate'] / 1000)
        print("Exiting requests manager\n", end="")

    def onlines_manager(self):
        while True:
            if self.data.close_event.is_set():
                break
            with self.data.lock:
                self.data.data_struct.check_onlines_data(self.data.basic_params['Removal_margin'])
            time.sleep(self.data.basic_params['Onlines_check_rate'] / 1000)
        print("Exiting onlines manager thread\n", end="")

    # packet related threads
    def process_packet_thread(self):
        while True:
            if self.data.close_event.is_set():
                break
            with self.data.lock:
                if not self.data.udp_receive_queue.empty():
                    p = self.data.udp_receive_queue.get()
                else:
                    if not self.data.tcp_receive_queue.empty():
                        p = self.data.tcp_receive_queue.get()
                    else:
                        continue
            if p.forwarding_counter > 1:
                # if forwarding is required then put it in the transmit queue
                p.forwarding_counter -= 1
                with self.data.lock:
                    self.data.udp_transmit_queue.put(p)
            # call the packet processing function
            with self.data.lock:
                if self.data.data_struct.should_process_packet(p):
                    DSPacket.packet_proc_funcs[p.type](p)
        print("Exiting received packet processing thread\n", end="")

    def online_packet_thread(self):
        while True:
            d = self.data.basic_params['O_Transmit_Rate'] / 1000
            time.sleep(d)

            if self.data.close_event.is_set():
                break
            with self.data.lock:
                if self.data.udp_transmit_queue.full():
                    continue
                p = O_packet(transmit_rate=self.data.basic_params['O_Transmit_Rate'],
                             alias=self.data.basic_params['Alias'],
                             packet_counter=self.data.basic_params['packet_counter'],
                             originator_packet_counter=self.data.basic_params['packet_counter'],
                             originator_ip=self.data.basic_params['IP_ADDR'],
                             sub_type=O_packet.SUB_TYPES_dict['default'],
                             forwarding_counter=1)
                self.data.udp_transmit_queue.put(p)
                self.data.log_info['Tran_o_packet_nos'] += 1
                self.data.basic_params['packet_counter'] += 1
                self.data.basic_params['packet_counter'] %= (2 ** 32)
        print("Exiting online packet generation thread\n", end="")

    def udp_transmit_thread(self):
        while True:
            if self.data.close_event.is_set():
                break
            with self.data.lock:
                if self.data.udp_transmit_queue.empty():
                    continue
                p = self.data.udp_transmit_queue.get()
            self.data.udp_transmit_socket.sendto(pk.dumps(p), (self.data.basic_params['Broadcast_addr'],
                                                               self.data.basic_params['UDP_Receive_port']))
            if self.data.is_verbose:
                outs = "Thread: udp_transmit_thread \n%s" % str(p)
                self.data.log_func(outs)
        self.data.udp_transmit_socket.close()
        print("UDP transmit stopped\n", end="")

    def udp_receive_thread(self):
        while True:
            if self.data.close_event.is_set():
                break
            try:
                data, addr = self.data.udp_receive_socket.recvfrom(1024)  # buffer size 1024
                p = pk.loads(data)

                with self.data.lock:
                    if self.data.udp_receive_queue.full():
                        self.data.log_func("UDP Receive queue is full ")
                        continue
                    self.data.udp_receive_queue.put(p)
                if self.data.is_verbose:
                    outs = "Thread: udp_receive_thread \n%s" % str(p)
                    self.data.log_func(outs)
            except socket.timeout:
                pass
        self.data.udp_receive_socket.close()
        print("UDP receive stopped\n", end="")

    def tcp_listen_thread(self):
        while True:
            if self.data.close_event.is_set():
                break
            try:
                conn, addr = self.data.tcp_listen_socket.accept()
                # self.data.out_func("Connection for a response got from: %s" % str(addr))
                th_rec = threading.Thread(target=self.tcp_receive_thread, args=(conn,))
                with self.data.lock:
                    self.data.threads.append(th_rec)
                th_rec.start()
            except socket.timeout:
                pass
        print("TCP listen stopped\n", end="")

    def tcp_receive_thread(self, conn):
        data = bytes()
        while True:
            data_tmp = conn.recv(1024)
            if not data_tmp:
                break
            data += data_tmp
        p = pk.loads(data)
        with self.data.lock:
            self.data.tcp_receive_queue.put(p)
        print("Exiting tcp receive thread\n", end="")

    def tcp_transmit_thread(self):
        while True:
            if self.data.close_event.is_set():
                break
            with self.data.lock:
                if self.data.tcp_transmit_queue.empty():
                    continue
                p = self.data.tcp_transmit_queue.get()
            tran_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tran_soc.settimeout(1)  # 1 sec for timeout
            ip = p.get_req_originator_ip()
            try:
                tran_soc.connect((ip, self.data.basic_params['TCP_Listen_port']))
                tran_soc.send(pk.dumps(p))
                tran_soc.close()
            except socket.timeout:
                print("Can't send response packet")

            if self.data.is_verbose:
                outs = "Thread: tcp_transmit_thread \n%s" % str(p)
                self.data.log_func(outs)
        print("TCP transmit stopped\n", end="")
