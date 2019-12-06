import pickle as pk

from packet import *


class DFSsysQueuePacketHandle:

    def __init__(self, data):
        self.data = data
        self.setup_packet_proc_funcs()

    # setting up the handlers
    def setup_packet_proc_funcs(self):
        DSPacket.set_packet_proc_func(O_packet.PACKET_TYPE, self.o_packet_proc)
        DSPacket.set_packet_proc_func(Req_packet.PACKET_TYPE, self.req_packet_proc)
        DSPacket.set_packet_proc_func(Res_packet.PACKET_TYPE, self.res_packet_proc)

    # handling the received online packets
    def o_packet_proc(self, p):
        self.data.log_info['Rece_o_packet_nos'] += 1
        # put the timestamp equal to time when received
        p.messages['Timestamp'] = int(round(time.time() * 1000))
        # add the user to the onlines table
        self.data.data_struct.add_item_onlines(p)
        self.data.data_struct.add_item_duplicate_packets(p)  # for testing only

    # handling the received request packets
    def req_packet_proc(self, p):
        self.data.log_info['Rece_req_packet_nos'] += 1
        self.data.data_struct.add_item_duplicate_packets(p)
        # make a response packet first
        p_res = Res_packet(req_originator_ip=p.originator_IP,
                           req_originator_counter=p.originator_packet_counter,
                           packet_counter=self.data.basic_params['packet_counter'],
                           originator_packet_counter=self.data.basic_params['packet_counter'],
                           originator_ip=self.data.basic_params['IP_ADDR'],
                           sub_type=p.sub_type, forwarding_counter=1)
        if p.sub_type == Res_packet.SUB_TYPES_dict['file']:
            if p.get_file_name() in self.data.data_struct.public_files:
                # send a response packet over UDP or TCP
                p_res.add_message('file', p.get_file_name())
        if p.sub_type == Res_packet.SUB_TYPES_dict['Online_users']:
            p_res.add_message('data', pk.dumps(self.data.data_struct.onlines))
        if p.sub_type == Res_packet.SUB_TYPES_dict['Public_files']:
            p_res.add_message('data', pk.dumps(self.data.data_struct.public_files))
        if p.sub_type == Res_packet.SUB_TYPES_dict['Private_files']:
            p_res.add_message('data', pk.dumps(self.data.data_struct.private_files))

        if p.get_transmit_type() == 0:
            p_res.forwarding_counter = 1
            self.data.tcp_transmit_queue.put(p_res)
        else:
            self.data.udp_transmit_queue.put(p_res)
        self.data.log_info['Tran_res_packet_nos'] += 1

    # handling the received response packets
    def res_packet_proc(self, p):
        if p.get_req_originator_ip() != self.data.basic_params['IP_ADDR']:
            return
        self.data.data_struct.add_item_duplicate_packets(p)
        # if the response is for me
        self.data.log_func("Got following response\n%s" % str(p), end="")
        self.data.log_info['Rece_res_packet_nos'] += 1

        key_list = list(self.data.requests_dict.keys())
        counter = p.get_req_originator_counter()
        if counter in key_list:
            # remove the key from the requests_dict and process the response
            self.data.requests_dict.pop(counter)
            # now process it depending on the response type and subtype
        # I guess lock can be released.
