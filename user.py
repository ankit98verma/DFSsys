import inspect
import ipaddress
import pickle as pk
import socket
import sys
import threading
from datetime import datetime
from queue import Queue

from PyQt5.QtWidgets import *

from data_structures import DataStructures
from dfssys_gui import DFSsysGUI
from packet import *
from strargparser import StrArgParser, CommandNotExecuted


class User:

    def welcome_msg(self):
        print("Welcome!\nStarting the UDP transmit and receive thread")

    def setup_packet_proc_funcs(self):
        DSPacket.set_packet_proc_func(O_packet.PACKET_TYPE, self.o_packet_proc)
        DSPacket.set_packet_proc_func(Req_packet.PACKET_TYPE, self.req_packet_proc)
        DSPacket.set_packet_proc_func(Res_packet.PACKET_TYPE, self.res_packet_proc)

    def read_config(self, path):
        req = {'IP_ADDR': str, 'UDP_Transmit_port': int, 'UDP_Receive_port': int, 'Listen_Conn_No': int,
               'O_Transmit_Rate': int, 'Alias': str,
               'Duplicate_packet_list_len': int, 'Removal_margin': int, 'Data_check_rate': int, 'GUI_update_rate': int,
               'Subnet_mask': str, 'UDP_transmit_queue_len': int, 'UDP_receive_queue_len': int}
        data = dict()
        f = open(path, 'r')
        for line in f.readlines():
            if line.strip(' ')[0] == "#":
                line = line.strip('#')
                line = line.strip('\n')
                words = line.split(':')
                data[words[0].strip(' ')] = req[words[0].strip(' ')](words[1].strip(' '))
        f.close()
        for r in req:
            if r not in data:
                print("Invalid '%s file: '%s' parameter is missing" % (path, r))
                exit(0)
        net = ipaddress.IPv4Network(data['IP_ADDR'] + '/' + data['Subnet_mask'], False)
        data['Broadcast_addr'] = str(net.broadcast_address)
        return data

    def __init__(self, path="user.config"):
        # initialize the protocol and operation related variable
        self.basic_params = self.read_config(path)
        self.basic_params['packet_counter'] = 0

        self.lock = threading.Lock()
        self.close_event = threading.Event()

        self.log_info = self.basic_params

        self.log_info['Tran_o_packet_nos'] = 0
        self.log_info['Tran_res_packet_nos'] = 0
        self.log_info['Tran_req_packet_nos'] = 0
        self.log_info['Rece_o_packet_nos'] = 0
        self.log_info['Rece_res_packet_nos'] = 0
        self.log_info['Rece_req_packet_nos'] = 0
        self.log_info['Tran_Req_packet_nos'] = 0
        self.log_info['Rece_Req_packet_nos'] = 0
        self.log_info['Tran_Res_packet_nos'] = 0
        self.log_info['Rece_Res_packet_nos'] = 0

        self.udp_transmit_queue = Queue(self.basic_params['UDP_transmit_queue_len'])
        self.udp_receive_queue = Queue(self.basic_params['UDP_receive_queue_len'])

        # setup UI
        self.UI = None

        # initialize operation related parameters
        self.par = StrArgParser("Main command parser")
        self.is_loop = True
        self.input_string = '>> '
        self.add_commands()
        self.welcome_msg()
        self.out_func = print
        self.out_file = None

        self.data = DataStructures(self.basic_params)

        # start and configure all threads
        self.is_verbose = False
        self.threads = []

        self.udp_transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_transmit_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_transmit_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.udp_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_receive_socket.bind((self.basic_params['IP_ADDR'], self.basic_params['UDP_Receive_port']))
        self.udp_receive_socket.settimeout(1)  # 1 sec timeout for now

        # setup the packet handle functions
        self.setup_packet_proc_funcs()
        self.start_threads()  # should be the last line in the __init__ function

    def start_threads(self):
        print("Starting the UDP thread")
        # thread for starting the UDP transmit
        th1 = threading.Thread(target=self.udp_transmit_thread, args=())
        self.threads.append(th1)

        # thread for starting the UDP receive
        th2 = threading.Thread(target=self.udp_receive_thread, args=())
        self.threads.append(th2)

        # thread for starting the regular checking of tables
        th3 = threading.Thread(target=self.check_onlines, args=())
        self.threads.append(th3)

        # thread for GUI
        th4 = threading.Thread(target=self.setup_main_gui, args=())
        self.threads.append(th4)

        th5 = threading.Thread(target=self.online_packet_thread, args=())
        self.threads.append(th5)

        # start all the threads
        th1.start()
        th2.start()
        th3.start()
        th4.start()
        th5.start()

    def setup_main_gui(self):
        app = QApplication([])
        self.UI = DFSsysGUI(self.log_info, self.data.onlines, self.data.duplicate_packets, self.lock)

        # thread for starting the regular checking of tables
        th = threading.Thread(target=self.trigger_UI, args=())
        self.threads.append(th)
        th.start()

        self.UI.show_guis('-a')
        app.exec_()
        print('Exited UI')

    def trigger_UI(self):
        while True:
            if self.close_event.is_set():
                break
            self.UI.trigger_guis('-a')
            time.sleep(self.basic_params['GUI_update_rate'] / 1000)  # trigger the update every 100 ms

    def check_onlines(self):
        while True:
            if self.close_event.is_set():
                break
            with self.lock:
                self.data.check_onlines_data(self.basic_params['Removal_margin'])
            time.sleep(self.basic_params['Data_check_rate'] / 1000)
        return

    def close_threads(self):
        for t in self.threads:
            t.join()

    def o_packet_proc(self, p):
        self.log_info['Rece_o_packet_nos'] += 1
        # put the timestamp equal to time when received
        p.messages['Timestamp'] = int(round(time.time() * 1000))
        # add the user to the onlines table
        self.data.add_item_onlines(p)
        self.data.add_item_duplicate_packets(p)  # for testing only

    def req_packet_proc(self, p):
        print('got req packet %s' % self.basic_params['IP_ADDR'])

    def res_packet_proc(self, p):
        print('got res packet %s' % self.basic_params['IP_ADDR'])

    def online_packet_thread(self):
        while True:
            d = self.basic_params['O_Transmit_Rate'] / 1000
            time.sleep(d)

            if self.close_event.is_set():
                break
            with self.lock:
                if self.udp_transmit_queue.full():
                    continue
                p = O_packet(transmit_rate=self.basic_params['O_Transmit_Rate'], alias=self.basic_params['Alias'],
                             packet_counter=self.basic_params['packet_counter'],
                             originator_packet_counter=self.basic_params['packet_counter'],
                             originator_ip=self.basic_params['IP_ADDR'],
                             sub_type=O_packet.SUB_TYPES_dict['default'],
                             forwarding_counter=1)
                self.udp_transmit_queue.put(p)
                self.basic_params['packet_counter'] = (self.basic_params['packet_counter'] + 1) % (2 ** 32)

    def udp_transmit_thread(self):
        while True:
            if self.close_event.is_set():
                break
            with self.lock:
                if self.udp_transmit_queue.empty():
                    continue
                p = self.udp_transmit_queue.get()
                self.udp_transmit_socket.sendto(pk.dumps(p), (self.basic_params['Broadcast_addr'],
                                                              self.basic_params['UDP_Receive_port']))
                self.log_info['Tran_o_packet_nos'] += 1
                if self.is_verbose:
                    outs = "Thread: udp_transmit_thread \n%s" % str(p)
                    self.out_func(outs)
        self.out_func("UDP transmit stopped\n", end="")
        self.udp_transmit_socket.close()

    def udp_receive_thread(self):
        while True:
            if self.close_event.is_set():
                break
            try:
                data, addr = self.udp_receive_socket.recvfrom(1024)  # buffer size 1024
                data = pk.loads(data)
                if self.is_verbose:
                    outs = "Thread: udp_receive_thread \n%s" % str(data)
                    self.out_func(outs)
                with self.lock:
                    if self.udp_receive_queue.full():
                        self.out_func("UDP Receive queue is full ")
                        continue
                    if self.data.should_process_packet(data):
                        DSPacket.packet_proc_funcs[data.type](data)
            except socket.timeout:
                pass
        self.out_func("UDP receive stopped\n", end="")
        self.udp_receive_socket.close()

    def add_commands(self):
        self.par.add_command("exit", "Ends the program", function=self.cmd_exit)

        self.par.add_command("set_bool", "Sets a boolean parameter", function=self.cmd_set_bool)
        self.par.get_command('set_bool').add_optional_arguments('-v', '--verbose',
                                                                'Sets the is_verbose flag to true or false. If verbose '
                                                                'flag is true then the system gives out all the output'
                                                                ' else it does not show the output of its '
                                                                'activities', param_type=bool)
        self.par.add_command("set_out", "Sets the output function to the file", function=self.cmd_set_out)
        self.par.get_command('set_out').add_optional_arguments('-fn', '--file_name',
                                                               'The name/address of the file to which the output of '
                                                               'the code will be written.')
        self.par.get_command('set_out').add_optional_arguments('-n', '--none',
                                                               'Reset the out stream to console print', param_type=None)

        self.par.add_command('start_script', "Runs the script.", function=self.cmd_start_script)
        self.par.get_command('start_script').add_compulsory_arguments('-fn', '--file_name',
                                                                      "The script file which is to be executed", )
        self.par.get_command('start_script').add_optional_arguments('-v', '--verbose',
                                                                    'Prints out the commands being executed from '
                                                                    'the script', param_type=None)

        self.par.add_command('show_gui', "Show different GUI windows.", function=self.cmd_show_gui)
        self.par.get_command('show_gui').add_optional_arguments('-m', '--main_gui',
                                                                'Shows the main GUI with basic log information',
                                                                param_type=None)
        self.par.get_command('show_gui').add_optional_arguments('-o', '--onlines_gui',
                                                                'Shows the list of online users',
                                                                param_type=None)
        self.par.get_command('show_gui').add_optional_arguments('-a', '--all',
                                                                'Shows the list of online users',
                                                                param_type=None)

        self.par.add_command('help', "Gives the details of all the commands of session management",
                             function=self.cmd_help)

    def cmd_exit(self, out_func=print):
        self.is_loop = False
        self.close_event.set()

        self.UI.close_guis()
        self.close_threads()
        out_func('Exiting')

        if self.out_file is not None:
            self.out_file.close()
        sys.exit(0)

    def cmd_help(self, res, out_func=print):
        self.par.show_help(res, out_func=out_func)

    def cmd_set_bool(self, res):
        key_list = list(res.keys())
        if '-v' in key_list:
            self.is_verbose = bool(res['-v'])

    def cmd_set_out(self, res):
        key_list = list(res.keys())
        if '-fn' in key_list:
            try:
                self.out_file = open(res['-fn'], 'w')
                self.out_func = self.write_file
            except FileNotFoundError:
                print("Wrong address")
        if '-n' in key_list:
            self.out_func = print
            self.out_file = None

    def cmd_show_gui(self, res):
        key_list = list(res.keys())
        with self.lock:
            print("alright!")
            self.UI.show_guis(key_list)

    def cmd_start_script(self, res, out_func=print):
        try:
            with open(res['-fn'], 'r') as f:
                for line in f:
                    line = line.replace('\t', ' ')
                    line = line.strip(' ')
                    line = line.strip('\n')
                    if line != '':
                        if '-v' in res:
                            out_func(self.input_string + line)
                        try:
                            self.is_loop = self.exec_cmd(line)
                        except CommandNotExecuted as e:
                            print(e)
                            break
                    if not self.is_loop:
                        break
        except FileNotFoundError:
            out_func('The file not found')
            raise CommandNotExecuted('start_script')
        except UnicodeDecodeError:
            out_func('The data in the file is corrupted')
            raise CommandNotExecuted('start_script')

    def write_file(self, line, end="\n"):
        readable = datetime.fromtimestamp(datetime.now().timestamp()).isoformat()
        write_str = readable + ":\n" + str(line) + end
        self.out_file.write(write_str)

    def handle_input(self):
        while self.is_loop:
            s = input(self.input_string).strip(' ')
            if len(s) == 0:
                continue
            try:
                self.is_loop = self.exec_cmd(s)
            except CommandNotExecuted as e:
                print(e)

    def exec_cmd(self, s):
        (cmd, res, func, out_func) = self.par.decode_command(s)
        if res is None:
            return True
        param_list = list(inspect.signature(func).parameters.keys())
        if 'res' in param_list and 'out_func' in param_list:
            func(res, out_func=out_func)
        elif 'res' in param_list:
            func(res)
        elif 'out_func' in param_list:
            func(out_func=out_func)

        if self.par.f_tmp is not None:
            self.par.f_tmp.close()
            self.par.f_tmp = None

        if cmd == 'exit':
            return False
        if cmd == 'start_script':
            return self.is_loop
        return True


if __name__ == '__main__':
    u = User()
    u.handle_input()
