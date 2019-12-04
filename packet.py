import time


class DSPacket:
    # PACKET_TYPES = {'O_packet':
    #                     {'Type': 0,
    #                      'Subtype':
    #                          {'Online_packet': 0}
    #                      },
    #                 'Req_packet':
    #                     {'Type': 1,
    #                      'Subtype':
    #                          {'File': 0,
    #                           'Online_users': 1,
    #                           'Public_files': 2,
    #                           'Sub_private_files': 3,
    #                           'Misce': 255}
    #                      },
    #                 'Res_packet':
    #                     {'Type': 2,
    #                      'Subtype':
    #                          {'File': 0,
    #                           'Online_users': 1,
    #                           'Public_files': 2,
    #                           'Sub_private_files': 3,
    #                           'Misce': 255}
    #                      }
    #                 }

    packet_proc_funcs = {}

    def __init__(self, packet_counter=0, originator_packet_counter=0, originator_ip="127.0.0.1",
                 packet_type=0, sub_type=0, forwarding_counter=0, messages=dict()):
        self.packet_length = len(list(messages.keys()))
        self.packet_counter = packet_counter
        self.originator_packet_counter = originator_packet_counter
        self.originator_IP = originator_ip
        self.type = packet_type
        self.sub_type = sub_type
        self.forwarding_counter = forwarding_counter
        self.messages = messages

    @staticmethod
    def set_packet_proc_func(packet_type, func):
        DSPacket.packet_proc_funcs[packet_type] = func

    def __str__(self):
        string = ""
        string += "Packet length: %d\n" % self.packet_length
        string += ("Packet counter: %d\n" % self.packet_counter)
        string += ("Originator Packet counter: %d\n" % self.originator_packet_counter)
        string += ("Originator IP: %s\n" % self.originator_IP)
        string += ("type: %d\n" % self.type)
        string += ("Sub type: %d\n" % self.sub_type)
        string += ("Forwarding counter: %d\n" % self.forwarding_counter)
        string += "Messages:\n"
        for k, v in self.messages.items():
            string += ("\tKey: %s, Value: %s\n" % (str(k), str(self.messages[k])))

        return string


class O_packet(DSPacket):
    PACKET_TYPE = 0
    SUB_TYPES = [0]
    SUB_TYPES_dict = {'default': 0}
    SUB_TYPES_rev = {0: 'default'}

    msg_keys = ['O_Transmit_Rate', 'Alias']

    def __init__(self, transmit_rate, alias, packet_counter=0, originator_packet_counter=0, originator_ip="127.0.0.1",
                 sub_type=0, forwarding_counter=0):
        super().__init__(packet_counter=packet_counter, originator_packet_counter=originator_packet_counter,
                         originator_ip=originator_ip, packet_type=O_packet.PACKET_TYPE, sub_type=sub_type,
                         forwarding_counter=forwarding_counter)
        self.messages['O_Transmit_Rate'] = transmit_rate
        self.messages['Alias'] = alias
        self.messages['Timestamp'] = int(round(time.time() * 1000))

    def get_transmit_rate(self):
        return self.messages['O_Transmit_Rate']

    def get_alias(self):
        return self.messages['Alias']

    def get_timestamp(self, formatted=False):
        return self.messages['Timestamp']


class Req_packet(DSPacket):
    PACKET_TYPE = 1
    SUB_TYPES = [0, 1, 2, 3, 255]
    SUB_TYPES_dict = {'file': 0, 'Online_users': 1, 'Public_files': 2, 'Sub_private_files': 3, 'Misce': 255}
    SUB_TYPES_rev = {0: 'file', 1: 'Online_users', 2: 'Public_files', 3: 'Sub_private_files', 255: 'Misce'}

    msg_keys = ['O_Transmit_Rate', 'Alias']

    def __init__(self, file_name="", packet_counter=0, originator_packet_counter=0, originator_ip="127.0.0.1",
                 sub_type=0, forwarding_counter=0):
        super().__init__(packet_counter=packet_counter, originator_packet_counter=originator_packet_counter,
                         originator_ip=originator_ip, packet_type=O_packet.PACKET_TYPE, sub_type=sub_type,
                         forwarding_counter=forwarding_counter)
        if self.sub_type == Req_packet.SUB_TYPES_dict['file']:
            self.messages = {'file': file_name}
        else:
            self.messages = {}


class Res_packet(DSPacket):
    PACKET_TYPE = 2
    SUB_TYPES = [0, 1, 2, 3, 255]
    SUB_TYPES_dict = {'file': 0, 'Online_users': 1, 'Public_files': 2, 'Sub_private_files': 3, 'Misce': 255}
    SUB_TYPES_rev = {0: 'file', 1: 'Online_users', 2: 'Public_files', 3: 'Sub_private_files', 255: 'Misce'}

    msg_keys = ['O_Transmit_Rate', 'Alias']

    def __init__(self, file_name="", packet_counter=0, originator_packet_counter=0, originator_ip="127.0.0.1",
                 sub_type=0, forwarding_counter=0):
        super().__init__(packet_counter=packet_counter, originator_packet_counter=originator_packet_counter,
                         originator_ip=originator_ip, packet_type=O_packet.PACKET_TYPE, sub_type=sub_type,
                         forwarding_counter=forwarding_counter)
        if self.sub_type == Req_packet.SUB_TYPES_dict['file']:
            self.messages = {'file': file_name}
        else:
            self.messages = {}
