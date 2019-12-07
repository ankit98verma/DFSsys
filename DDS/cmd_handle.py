import inspect
import sys
from datetime import datetime
from DDS.packet import *
from DDS.strargparser import *


class DFSsysCmdHandle:

    def __init__(self, data):
        self.data = data
        self.par = StrArgParser("Main command parser")
        self.is_loop = True
        self.input_string = '>> '
        self.add_commands()

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

        self.par.add_command('show_data', "Show different GUI windows.", function=self.cmd_show_data)
        self.par.get_command('show_data').add_optional_arguments('-o', '--onlines_gui',
                                                                 'Shows the list of online users',
                                                                 param_type=None)
        self.par.get_command('show_data').add_optional_arguments('-l', '--log_data',
                                                                 'Shows the log data',
                                                                 param_type=None)
        self.par.get_command('show_data').add_optional_arguments('-pubf', '--public_files',
                                                                 'Shows the list of public files',
                                                                 param_type=None)
        self.par.get_command('show_data').add_optional_arguments('-prif', '--private_files',
                                                                 'Shows the list of private files',
                                                                 param_type=None)

        self.par.add_command('req', "Sends request packet", function=self.cmd_req)
        self.par.get_command('req').add_optional_arguments('-f', '--file', 'Request a file', param_type=None)
        self.par.get_command('req').add_optional_arguments('-o', '--onlines', 'Request the list of online users',
                                                           param_type=None)
        self.par.get_command('req').add_optional_arguments('-pubf', '--public_files', 'Request the list of public files'
                                                           , param_type=None)
        self.par.get_command('req').add_optional_arguments('-prif', '--private_files', 'Request the list of public '
                                                                                       'files ', param_type=None)

        self.par.add_command('help', "Gives the details of all the commands of session management",
                             function=self.cmd_help)

    def cmd_exit(self, out_func=print):
        self.is_loop = False
        self.data.close_event.set()

        try:
            self.data.UI.close_guis()
        except AttributeError:
            pass
        for t in self.data.threads:
            t.join()
        out_func('Exiting')

        if self.data.log_file is not None:
            self.data.log_file.close()
        input(self.input_string + "Press enter (return) key to exit")
        sys.exit(0)

    def cmd_help(self, res, out_func=print):
        self.par.show_help(res, out_func=out_func)

    def cmd_set_bool(self, res):
        key_list = list(res.keys())
        if '-v' in key_list:
            self.data.is_verbose = bool(res['-v'])

    def cmd_set_out(self, res):
        key_list = list(res.keys())
        if '-fn' in key_list:
            try:
                self.data.log_file = open(res['-fn'], 'w')
                self.data.log_func = self.write_file
            except FileNotFoundError:
                print("Wrong address")
        if '-n' in key_list:
            self.data.log_func = print
            self.data.log_file = None

    def cmd_show_data(self, res):
        key_list = list(res.keys())
        if '-o' in key_list:
            with self.data.lock:
                if len(self.data.data_struct.onlines) > 0:
                    keys = list(self.data.data_struct.onlines[0].keys())
                    for k in keys:
                        print("%s\t\t" % k, end="")
                    print()
                    for j in self.data.data_struct.onlines:
                        for _, v in j.items():
                            print("%s\t\t" % str(v), end="")
                        print()
        if '-pubf' in key_list:
            with self.data.lock:
                print("Following are the public files")
                for j in self.data.data_struct.public_files:
                    print("\t%s" % j)
        if '-prif' in key_list:
            with self.data.lock:
                print("Following are the private files")
                for j in self.data.data_struct.private_files:
                    print("\t%s" % j)
        if '-l' in key_list:
            with self.data.lock:
                print("Following are the log files")
                print("Key\t\tValue")
                for k, v in self.data.log_info.items():
                    print("%s\t\t%s" % (str(k), str(v)))

    def cmd_req(self, res):
        key_list = list(res.keys())

        if '-f' in key_list:
            fn = input(self.input_string + "Enter file name (with file type extension):")
            p = Req_packet(res_type=self.data.basic_params['Response_over_type'], file_name=fn,
                           packet_counter=self.data.basic_params['packet_counter'],
                           originator_packet_counter=self.data.basic_params['packet_counter'],
                           originator_ip=self.data.basic_params['IP_ADDR'],
                           sub_type=Res_packet.SUB_TYPES_dict['file'],
                           forwarding_counter=1)
            with self.data.lock:
                for i in range(0, self.data.basic_params['Burst_nos']):
                    self.data.add_to_transmit_queue(self.data.udp_transmit_queue, p)
                self.data.add_to_transmit_queue(self.data.udp_transmit_queue, p)
                self.data.responses_dict[p.packet_counter] = {'start_proc': 0, 'list': []}
                self.data.requests_dict[p.packet_counter] = int(round(time.time() * 1000))

        if '-o' in key_list:
            p = Req_packet(res_type=self.data.basic_params['Response_over_type'],
                           packet_counter=self.data.basic_params['packet_counter'],
                           originator_packet_counter=self.data.basic_params['packet_counter'],
                           originator_ip=self.data.basic_params['IP_ADDR'],
                           sub_type=Res_packet.SUB_TYPES_dict['Online_users'],
                           forwarding_counter=1)
            with self.data.lock:
                for i in range(0, self.data.basic_params['Burst_nos']):
                    self.data.add_to_transmit_queue(self.data.udp_transmit_queue, p)
                self.data.add_to_transmit_queue(self.data.udp_transmit_queue, p)
                self.data.responses_dict[p.packet_counter] = {'start_proc': 0, 'list': []}
                self.data.requests_dict[p.packet_counter] = int(round(time.time() * 1000))

        if '-pubf' in key_list:
            p = Req_packet(res_type=self.data.basic_params['Response_over_type'],
                           packet_counter=self.data.basic_params['packet_counter'],
                           originator_packet_counter=self.data.basic_params['packet_counter'],
                           originator_ip=self.data.basic_params['IP_ADDR'],
                           sub_type=Res_packet.SUB_TYPES_dict['Public_files'],
                           forwarding_counter=1)
            with self.data.lock:
                for i in range(0, self.data.basic_params['Burst_nos']):
                    self.data.add_to_transmit_queue(self.data.udp_transmit_queue, p)
                self.data.responses_dict[p.packet_counter] = {'start_proc': 0, 'list': []}
                self.data.requests_dict[p.packet_counter] = int(round(time.time() * 1000))

        if '-prif' in key_list:
            p = Req_packet(res_type=self.data.basic_params['Response_over_type'],
                           packet_counter=self.data.basic_params['packet_counter'],
                           originator_packet_counter=self.data.basic_params['packet_counter'],
                           originator_ip=self.data.basic_params['IP_ADDR'],
                           sub_type=Res_packet.SUB_TYPES_dict['Private_files'],
                           forwarding_counter=1)
            with self.data.lock:
                for i in range(0, self.data.basic_params['Burst_nos']):
                    self.data.add_to_transmit_queue(self.data.udp_transmit_queue, p)
                self.data.add_to_transmit_queue(self.data.udp_transmit_queue, p)
                self.data.responses_dict[p.packet_counter] = {'start_proc': 0, 'list': []}
                self.data.requests_dict[p.packet_counter] = int(round(time.time() * 1000))

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
            out_func('The data_struct in the file is corrupted')
            raise CommandNotExecuted('start_script')

    def write_file(self, line, end="\n"):
        readable = datetime.fromtimestamp(datetime.now().timestamp()).isoformat()
        write_str = readable + ":\n" + str(line) + end
        self.data.log_file.write(write_str)

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
