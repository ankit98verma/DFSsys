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
        # if p.type == DS_packet.PACKET_TYPES['O_packet']['Type']:
        #     return True
        if self.is_duplicate(p):
            return False

    def is_duplicate(self, p):
        k = [i for i in self.duplicate_packets if (i['originator_IP'] == p.originator_IP and
                                                   i['originator_packet_counter'] == p.originator_packet_counter)]
        return len(k) > 0

    def add_item_duplicate_packets(self, p):
        d = {'originator_IP': p.originator_IP, 'originator_packet_counter': p.originator_packet_counter}
        self.duplicate_packets.append(d)
        return
