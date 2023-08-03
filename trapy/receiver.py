import packet
import socket


class Receiver:

    def __init__(self,listening_port,sender_ip, sender_port,init_sq_number):
        self.listening_port = listening_port
        self.sender_ip = sender_ip
        self.sender_port = sender_port
        self.init_sq_number = init_sq_number
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)

        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

       
        self.last_pack = None


    def recv(self,length):
        data = bytes()
        expected_sq = self.init_sq_number
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        while len(data) < length:
            
            rcv_pack = self.socket.recvfrom(65565)[0][20:]
           

            source_port, destination_port, seq_num, ack_num, flags, checksum, receive_window, urgent_data_pointer = packet.Packet.get_header(rcv_pack)
            
            if destination_port != self.listening_port or source_port != self.sender_port or (flags & (1<<4)):
                continue 
            
            if seq_num ==0:
                continue
           
            
            if not packet.Packet.verify_checksum(rcv_pack):
                print('corrupt')
                if self.last_pack != None:
                    s.sendto(self.last_pack.to_bytes(), (self.sender_ip,self.sender_port))
                continue
            
           
            if expected_sq == seq_num:
                t = len(data)
                recv_data = packet.Packet.get_data(rcv_pack)
                if t + len(recv_data) > length:
                    recv_data = recv_data[:(length-t)]
                
                
                data += recv_data
                expected_sq +=1
                ack_packet = packet.Packet(self.listening_port, self.sender_port,expected_sq-1,expected_sq)
                ack_packet.ack = True
                self.last_pack = ack_packet
                s.sendto(ack_packet.to_bytes(), (self.sender_ip,self.sender_port))
            
            else:
                if self.last_pack != None:
                    s.sendto(self.last_pack.to_bytes(), (self.sender_ip,self.sender_port))

            
            if flags & 1:
                break
        
        return data