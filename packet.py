
class DS_packet:

    def __init__(self, packet_counter=0, originator_packet_counter=0,
                 packet_type=0, sub_type=0, forwarding_counter=0, messages=dict()):
        self.packet_length = len(list(messages.keys()))
        self.packet_counter = packet_counter
        self.originator_packet_counter = originator_packet_counter
        self.type = packet_type
        self.sub_type = sub_type
        self.forwarding_counter = forwarding_counter
        self.messages = messages

    def __repr__(self):
        print("Packet length: %d" % self.packet_length)
        print("Packet counter: %d" % self.packet_counter)
        print("Originator Packet counter: %d" % self.originator_packet_counter)
        print("type: %d" % self.type)
        print("Sub type: %d" % self.sub_type)
        print("Forwarding counter: %d" % self.forwarding_counter)
        for k, v in self.messages.items():
            print("Key: %s, Value: %s" % (str(k), str(self.messages[k])))
