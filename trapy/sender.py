import select
import packet
import datetime
import utils
import socket

class Sender:
    def __init__(self,remote_host,remote_port, host_port, init_sq_number=0):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.init_sq_number = init_sq_number
        self.estimated_rtt = 1.5
        self.timeout_interval = 1.8
        self.packet_size = 4096
        self.host_port = host_port
        self.rtt = {}
        self.expected_ack_num = init_sq_number
        self.is_retransmit = False
        self.send_lenght = 0

        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.recv_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

       

    def rdt(self,data):
        self.estimated_rtt = 1.5
        self.timeout_interval = 1.8
        self.rtt = {}
        self.expected_ack_num = self.init_sq_number
        self.is_retransmit = False
        
        self.send_lenght = 0

        

        pack_data = []
        i=0
        while(i < len(data)):
            pack_data += [data[i:i+self.packet_size]]
            i+= self.packet_size

        packets = self.__make_packets(pack_data)
        
        next_to_send = 0
        base = 0
        windows_size = 23
        timeout_cnt = 0
        while base < len(packets):
            limit = base + windows_size
            while next_to_send < limit:
                if next_to_send >= len(packets):
                    break
                
                
                self.__transmit(packets[next_to_send])
                next_to_send +=1
            
            while True:
                ready_to_read, ready_to_write, in_error = \
                select.select(
                    [self.recv_socket],
                    [],
                    [],
                    self.timeout_interval)
                
                if ready_to_read:
                    try:
                        ack_pack = self.recv_socket.recvfrom(65535)[0][20:]
                       
                        source_port, destination_port, seq_num, ack_num, flags, checksum, receive_window,  urgent_data_pointer = packet.Packet.get_header(ack_pack)
                        
                        if destination_port !=  self.host_port or source_port != self.remote_port or not (flags & 1 <<4):
                            continue
                        
                        

                        if not packet.Packet.verify_checksum(ack_pack):
                            continue

                        if seq_num ==0:
                            continue
                        
                     
                        
                       
                        if not self.is_retransmit:
                            try:
                                sample_rtt = (datetime.datetime.now() - self.rtt[seq_num]).total_seconds()     
                                if self.estimated_rtt == 1.5:
                                    self.estimated_rtt = sample_rtt
                                self.timeout_interval, self.estimated_rtt = utils.update_rtt(self.estimated_rtt,sample_rtt)
                            except:
                                pass
                        
                        if (ack_num - self.init_sq_number) > base:
                           
                            base = ack_num - self.init_sq_number
                            timeout_cnt = 0
                        if ack_num == self.expected_ack_num:
                            self.is_retransmit = False
                            break

                    except Exception as e:
                        pass
                        #print('Failed to receive ack from the receiver: ' + e.message)
                
                else: 
                    if timeout_cnt == 10:
                        #print('Timeout 6 times, exiting...')
                        return self.send_lenght

                    self.is_retransmit = True
                    self.__retransmit(packets,base,limit)
                    timeout_cnt +=1

        return self.send_lenght

                
    
    def __transmit(self, packet: packet.Packet, is_retransmit = False):
        send_time = datetime.datetime.now()
        if not is_retransmit:
            self.rtt[packet.seq_number] = send_time  
            self.expected_ack_num = packet.seq_number + 1
            self.send_lenght += len(packet.data)
        
        self.socket.sendto(packet.to_bytes(), (self.remote_host,self.remote_port))
    
    def __retransmit(self, packets, base, limit):
        next_to_send = base
        while next_to_send < limit:
            if next_to_send >= len(packets):
                break
            self.__transmit(packets[next_to_send], True)
            next_to_send += 1
    
    def __make_packets(self,pack_data):
        packets = []
        for (i,pd) in enumerate(pack_data):
            packets.append(packet.Packet(self.host_port,self.remote_port,self.init_sq_number+i,self.init_sq_number+i,pd))
        
        packets[-1].fin = True
        return packets
