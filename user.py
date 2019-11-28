import inspect
import pickle as pk
import socket
import threading
import time
from datetime import datetime

from data_structures import DataStructures
from packet import DS_packet
from strargparser import StrArgParser, CommandNotExecuted


class User:

    def welcome_msg(self):
        print("Welcome!\nStarting the UDP transmit and receive thread")

    def setup_packet_proc_funcs(self):
        DS_packet.set_packet_proc_func(DS_packet.PACKET_TYPES['O_packet']['Type'], self.o_packet_proc)
        DS_packet.set_packet_proc_func(DS_packet.PACKET_TYPES['Req_packet']['Type'], self.req_packet_proc)
        DS_packet.set_packet_proc_func(DS_packet.PACKET_TYPES['Res_packet']['Type'], self.res_packet_proc)

    def __init__(self, path="user.config"):
        self.basic_params = dict()
        f = open(path, 'r')

        # list of all the configuration parameters to be present in s.config
        rq = ['IP_ADDR', 'UPD_Transmit_port', 'UPD_Receive_port', 'Listen_Conn_No', 'O_Transmit_Rate', 'Broadcast_addr']
        for line in f.readlines():
            if line[0] == "#":
                line = line.strip('#')
                words = line.split(':')
                self.basic_params[words[0].strip()] = words[1].strip()
        for r in rq:
            if r not in self.basic_params:
                print("Invalid '%s file: '%s' parameter is missing" % (path, r))
                exit(0)

        # initialize operation related parameters
        self.par = StrArgParser("Main command parser")
        self.is_loop = True
        self.input_string = '>> '
        self.add_commands()
        self.welcome_msg()
        self.out_func = print
        self.out_file = None

        # initialize the protocol related variable
        self.prev_packet = None
        self.basic_params['packet_counter'] = 0

        self.data = DataStructures(self.basic_params)

        # start and configure all threads
        self.threads = []

        self.udp_transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_transmit_socket.bind((self.basic_params['IP_ADDR'], int(self.basic_params['UPD_Transmit_port'])))
        self.udp_transmit_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.is_udp_transmit = True
        self.is_verbose = False

        self.udp_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_receive_socket.bind((self.basic_params['IP_ADDR'], int(self.basic_params['UPD_Receive_port'])))
        self.udp_receive_socket.settimeout(1)  # 1 sec timeout for now
        self.is_udp_receive = True

        self.setup_packet_proc_funcs()
        self.start_threads()  # should be the last line in the __init__ function

    def start_threads(self):
        print("Starting the UDP thread")
        th1 = threading.Thread(target=self.udp_transmit_thread, args=())
        self.threads.append(th1)

        th2 = threading.Thread(target=self.udp_receive_thread, args=())
        self.threads.append(th2)
        # init more threads
        th1.start()
        th2.start()

    def close_threads(self):
        for t in self.threads:
            t.join()

    def o_packet_proc(self):
        print('got o_packet')

    def req_packet_proc(self):
        print('got req packet')

    def res_packet_proc(self):
        print('got res packet')

    def udp_transmit_thread(self):
        while self.is_udp_transmit:
            #  make the online packets
            p_msg = {'O_Transmit_Rate': self.basic_params['O_Transmit_Rate'],
                     'Alias': self.basic_params['Alias']}
            p = DS_packet(self.basic_params['packet_counter'], self.basic_params['packet_counter'],
                          originator_ip=self.basic_params['IP_ADDR'],
                          packet_type=DS_packet.PACKET_TYPES['O_packet']['Type'],
                          sub_type=DS_packet.PACKET_TYPES['O_packet']['Subtype']['Online_packet'],
                          forwarding_counter=1, messages=p_msg)
            self.basic_params['packet_counter'] = (self.basic_params['packet_counter'] + 1) % (2 ** 32)
            self.udp_transmit_socket.sendto(pk.dumps(p), (self.basic_params['Broadcast_addr'],
                                                          int(self.basic_params['UPD_Receive_port'])))
            if self.is_verbose:
                outs = "Thread: udp_transmit_thread \n%s" % str(p)
                self.out_func(outs)
            d = int(self.basic_params['O_Transmit_Rate']) / 1000

            time.sleep(d)
        self.out_func("UDP transmit stopped\n", end="")
        self.udp_transmit_socket.close()

    def udp_receive_thread(self):
        while self.is_udp_receive:
            try:
                data, addr = self.udp_receive_socket.recvfrom(1024)  # buffer size 1024
                print(addr)
                data = pk.loads(data)
                if self.is_verbose:
                    outs = "Thread: udp_receive_thread \n%s" % str(data)
                    self.out_func(outs)
                #     should we process the packet now???
                if self.data.should_process_packet(data):
                    DS_packet.packet_proc_funcs[data.type]()
                else:
                    print("Nope :(")

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

        self.par.add_command('help', "Gives the details of all the commands of session management",
                             function=self.cmd_help)

    def cmd_exit(self, out_func=print):
        self.is_loop = False
        self.is_udp_transmit = False
        self.is_udp_receive = False

        self.close_threads()
        out_func('Exiting')

        if self.out_file is not None:
            self.out_file.close()
        exit(0)

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
