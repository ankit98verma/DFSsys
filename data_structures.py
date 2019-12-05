import ipaddress
from queue import Queue

from packet import *


class DFSsysData:

    def __init__(self, path):
        self.path = path
        self.basic_params = self.read_config()
        self.basic_params['packet_counter'] = 0

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

    def read_config(self):
        req = {'IP_ADDR': str, 'UDP_Transmit_port': int, 'UDP_Receive_port': int, 'Listen_Conn_No': int,
               'O_Transmit_Rate': int, 'Alias': str,
               'Duplicate_packet_list_len': int, 'Removal_margin': int, 'Data_check_rate': int,
               'GUI_update_rate': int,
               'Subnet_mask': str, 'UDP_transmit_queue_len': int, 'UDP_receive_queue_len': int}
        data = dict()
        f = open(self.path, 'r')
        for line in f.readlines():
            if line.strip(' ')[0] == "#":
                line = line.strip('#')
                line = line.strip('\n')
                words = line.split(':')
                data[words[0].strip(' ')] = req[words[0].strip(' ')](words[1].strip(' '))
        f.close()
        for r in req:
            if r not in data:
                print("Invalid '%s file: '%s' parameter is missing" % (self.path, r))
                exit(0)
        net = ipaddress.IPv4Network(data['IP_ADDR'] + '/' + data['Subnet_mask'], False)
        data['Broadcast_addr'] = str(net.broadcast_address)
        return data
class DataStructures:

    def __init__(self, basic_params):
        self.onlines = []
        self.public_files = []
        self.sub_private_files = []
        self.private_files = []
        self.duplicate_packets = []

        self.basic_params = basic_params

    def should_process_packet(self, p):
        # if p.originator_IP == self.basic_params['IP_ADDR']:
        #     return False
        if p.type == O_packet.PACKET_TYPE:
            return True
        if self.is_duplicate(p):
            return False
        return True

    def add_item_onlines(self, p):
        ind = [self.onlines.index(l) for l in self.onlines if l['IP_addr'] == p.originator_IP]
        if len(ind) == 1:
            self.onlines[ind[0]]['alias'] = p.get_alias()
            self.onlines[ind[0]]['o_transmit_rate'] = p.get_transmit_rate()
            self.onlines[ind[0]]['timestamp'] = p.get_timestamp()
        else:
            d = {'IP_addr': p.originator_IP, 'alias': p.get_alias(), 'o_transmit_rate': p.get_transmit_rate(),
                 'timestamp': p.get_timestamp()}
            self.onlines.append(d)
        return

    def check_onlines_data(self, removal_margin):
        curr_time = int(round(time.time() * 1000))
        for i in self.onlines:
            if (curr_time - i['timestamp']) > (removal_margin + i['o_transmit_rate']):
                self.onlines.remove(i)
        return

    def add_item_duplicate_packets(self, p):
        d = {'originator_IP': p.originator_IP, 'originator_packet_counter': p.originator_packet_counter}
        self.duplicate_packets.append(d)
        if len(self.duplicate_packets) > self.basic_params['Duplicate_packet_list_len']:
            self.duplicate_packets.remove(self.duplicate_packets[0])
        return

    def is_duplicate(self, p):
        k = [i for i in self.duplicate_packets if (i['originator_IP'] == p.originator_IP and
                                                   i['originator_packet_counter'] == p.originator_packet_counter)]
        return len(k) > 0
