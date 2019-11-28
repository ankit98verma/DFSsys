import inspect
import socket
import threading
import time

from strargparser import StrArgParser, CommandNotExecuted


class User:

    def __init__(self, path="user.config"):
        self.params = dict()
        f = open(path, 'r')

        # list of all the configuration parameters to be present in s.config
        rq = ['IP_ADDR', 'UPD_Transmit_port', 'UPD_Receive_port', 'Listen_Conn_No', 'O_Transmit_Rate']
        for l in f.readlines():
            if l[0] == "#":
                l = ((l[1:]).strip())
                words = l.split(':')
                self.params[words[0].strip()] = words[1].strip()
        for r in rq:
            if r not in self.params:
                print("Invalid 's.config' file: '%s' parameter is missing" % r)
                exit(0)

        self.par = StrArgParser("Main command parser")
        self.is_loop = True
        self.input_string = '>> '
        self.add_commands()

        self.welcome_msg()

        self.threads = []

        self.udp_transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_transmit_socket.bind((self.params['IP_ADDR'], int(self.params['UPD_Transmit_port'])))
        self.udp_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_receive_socket.bind((self.params['IP_ADDR'], int(self.params['UPD_Receive_port'])))
        self.udp_receive_socket.settimeout(1)  # 1 sec timeout for now
        self.is_udp_transmit = True
        self.is_udp_receive = True

        # self.start_threads()    # should be the last line in the __init__ function

    def start_threads(self):
        print("Starting the UDP thread")
        th1 = threading.Thread(target=self.udp_transmit_thread, args=())
        self.threads.append(th1)

        th2 = threading.Thread(target=self.udp_receive_thread, args=())
        self.threads.append(th2)
        # init more threads
        th1.start()
        th2.start()

    def udp_transmit_thread(self):
        while self.is_udp_transmit:
            #  make the online packet
            self.udp_transmit_socket.sendto(bytes("hi", "utf-8"),
                                            (self.params['IP_ADDR'], int(self.params['UPD_Receive_port'])))
            d = int(self.params['O_Transmit_Rate']) / 1000

            time.sleep(d)
            print("done")  # only for test
        print("UDP transmit stopped\n", end="")
        self.udp_transmit_socket.close()

    def udp_receive_thread(self):
        while self.is_udp_receive:
            try:
                data, addr = self.udp_receive_socket.recvfrom(1024)  # buffer size 1024
                print("Data: %s, Addr: %s" % (data.decode(), addr))
            except socket.timeout:
                pass
        print("UDP receive stopped\n", end="")
        self.udp_receive_socket.close()

    def add_commands(self):
        self.par.add_command("exit", "Ends the program", function=self.cmd_exit)

        # self.par.add_command("start_thread", "Starts a thread", function=self.start_thread)
        # self.par.get_command('start_session').add_optional_arguments('-sd', '--start_date',
        #                                                              'The start date in YYYY-MM-DD format'
        #                                                              '. Enter "exit" to use default '
        #                                                              'analysis duration')
        #
        # self.par.add_command('load_session', "Loads a previously saved session", function=self.cmd_load_session)
        # self.par.get_command('load_session').add_compulsory_arguments('-fn', '--file_name',
        #                                                               'The name/address of the file from '
        #                                                               'which the session is to be loaded')
        #
        # self.par.add_command('start_script', "Runs the script.", function=self.cmd_start_script)
        # self.par.get_command('start_script').add_compulsory_arguments('-fn', '--file_name',
        #                                                               "The script file which is to be executed", )
        # self.par.get_command('start_script').add_optional_arguments('-v', '--verbose',
        #                                                             'Prints out the commands being executed from '
        #                                                             'the script', param_type=None)

        self.par.add_command('help', "Gives the details of all the commands of session management",
                             function=self.cmd_help)

    def cmd_exit(self, out_func=print):
        self.is_loop = False
        self.is_udp_transmit = False
        self.is_udp_receive = False
        out_func('Exiting')
        exit(0)

    def cmd_help(self, res, out_func=print):
        self.par.show_help(res, out_func=out_func)

    def handle_input(self):
        while self.is_loop:
            s = input(self.input_string).strip(' ')
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

    def close_threads(self):
        for t in self.threads:
            t.join()

    def welcome_msg(self):
        print("Welcome!\nStarting the UDP transmit and receive thread")


if __name__ == '__main__':
    u = User()
    u.handle_input()
