import struct
import utils

class Packet:
    
    def __init__(self,Src_port,Dest_port,Seq_number=0,Ack_number=0,Data = bytes()):

        self.src_port = Src_port # 16 bit
        self.dest_port = Dest_port # 16 bit
        self.seq_number = Seq_number # 32 bit
        self.ack_number = Ack_number # 32 bit
        self.cwr = 0 # 1 bit
        self.ece = 0 # 1 bit 
        self.urg = 0 # 1 bit
        self.ack = 0 # 1 bit
        self.psh = 0 # 1 bit
        self.rst = 0 # 1 bit
        self.syn = 0 # 1 bit
        self.fin = 0 # 1 bit
        self.data = Data 
        self.checksum = 0 # 16 bit
        self.receive_window = 0 #16 bit
        self.urgent_data_pointer = 0  # 16-bit 
        self.flags = 0 # 8 bit
    
    def to_bytes(self):
        self.flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5) + (self.cwr << 6) + (self.ece << 7)
        
        bit_header = struct.pack('!HHIIBHHH',self.src_port,self.dest_port,self.seq_number,self.ack_number,\
                                self.flags,\
                                self.checksum, self.receive_window, self.urgent_data_pointer)
        
        self.checksum = utils.checksum(bit_header + self.data)
        
        bit_header = struct.pack('!HHIIBHHH',self.src_port,self.dest_port,self.seq_number,self.ack_number,\
                                self.flags,\
                                self.checksum, self.receive_window, self.urgent_data_pointer)
        
        packet_in_bytes = bit_header + self.data
        return packet_in_bytes
    
    @staticmethod
    def get_header(packet):
        source_port, destination_port, seq_num, ack_num, flags, checksum, receive_window, urgent_data_pointer = struct.unpack('!HHIIBHHH', packet[:19])

        return source_port, destination_port, seq_num, ack_num, flags, checksum, receive_window,  urgent_data_pointer

    @staticmethod
    def get_data(packet):
        return packet[19:]

    @staticmethod
    def verify_checksum(packet):
        src_port, dest_port, seq_number, ack_number, flags, checksum, receive_window,  urgent_data_pointer = Packet.get_header(packet)
        
        rcv_checksum = checksum
        
        checksum = 0 
        bit_header = bit_header = struct.pack('!HHIIBHHH',src_port,dest_port,seq_number,ack_number,\
                                flags,\
                                checksum, receive_window, urgent_data_pointer)
        data = Packet.get_data(packet)
        checksum = utils.checksum(bit_header+data)

        return checksum == rcv_checksum
