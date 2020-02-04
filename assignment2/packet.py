# Methods for working with packets, such as crafting and extracting data

class Packet:
    def __init__(self, packet_length):
        self.packet_length = packet_length


    def create(self, seq_num):
        seq_bytes = seq_num.to_bytes(self.packet_length,
                                    byteorder='big', signed=True)
        return seq_bytes

    def extract(self, packet):
        seq_num = int.from_bytes(packet, 
                                byteorder='big', signed=True)
        return seq_num
