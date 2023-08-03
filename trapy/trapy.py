import utils
import socket
import packet
import select
import sender
import receiver
import random

class Conn:

    binded = {}
    local_port = 3000
    
    def __init__(self, address = ''):
        self.local_add = address
        self.remote_add = ''
        self.sender = None
        self.receiver = None
        self.is_close = False
        self.send_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)

    
    def listen(self):
        Conn.bind(self.local_add)

    @staticmethod
    def bind(address):
        try:
            s = Conn.binded[address]
            raise ConnException('Address already in use')
        except KeyError:
            Conn.binded[address] = True

    def dial(self,addres):
        host,port = utils.parse_address(addres)
        while True:
            try:
                Conn.binded[Conn.local_port]
                Conn.local_port +=1
            except KeyError:
                break
        my_port = Conn.local_port
        Conn.local_port +=1

        init_sq_number = random.randint(1,500)
        pack = packet.Packet(my_port,port, init_sq_number)
        pack.syn = True
        pack = pack.to_bytes()
        
        send_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        recv_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        recv_s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        

        self.sender = sender.Sender(host,port,my_port,init_sq_number)

        send_s.sendto(pack,(host,port))
        while(True):
            ready_to_read, ready_to_write, in_error = \
                select.select(
                    [recv_s],
                    [],
                    [],
                    1.5)
            
            if ready_to_read :
                syn_ack_pack = recv_s.recvfrom(65535)[0][20:]
                source_port, destination_port, seq_num, ack_num, flags, checksum, receive_window,  urgent_data_pointer = packet.Packet.get_header(syn_ack_pack)

                if destination_port != my_port:
                    continue
                if not packet.Packet.verify_checksum(syn_ack_pack):
                    continue

                if (flags & (1<<1) ) and (flags & (1<<4) ) and (ack_num == init_sq_number + 1 ) :
                    self.receiver = receiver.Receiver(my_port,host,port,seq_num)
                    break
            else:
                send_s.sendto(pack,(host,port))
        
        ack_pack = packet.Packet(my_port,port,0,self.receiver.init_sq_number +1)
        ack_pack.ack = True
        send_s.sendto(ack_pack.to_bytes(),(host,port))

       
        
        
    def accept(self):

        a_conn = Conn()
        a_conn.local_add = self.local_add
        a_conn.remote_add = self.remote_add

        
        if not Conn.binded[self.local_add]:
            return ConnException(str(self.local_add)+ 'has not been put in listen')
        
        send_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        recv_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        recv_s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        host,port = utils.parse_address(self.local_add)
        recv_s.bind((host,port))

        while True:
            data, add = recv_s.recvfrom(65535)
            sender_ip = add[0]
            syn_pack = data[20:]

            source_port, destination_port, seq_num, ack_num, flags, checksum, receive_window,  urgent_data_pointer = packet.Packet.get_header(syn_pack)

            if destination_port != port:
                continue
            
            if not packet.Packet.verify_checksum(syn_pack):
                continue
                
            if flags & (1<<1):
                a_conn.receiver = receiver.Receiver(port,sender_ip,source_port,seq_num)
                break

        init_sq_number = random.randint(1,500)
        syn_ack_pack = packet.Packet(port,a_conn.receiver.sender_port,init_sq_number,a_conn.receiver.init_sq_number + 1)
        syn_ack_pack.syn = True
        syn_ack_pack.ack = True
        syn_ack_pack = syn_ack_pack.to_bytes()
        a_conn.sender = sender.Sender(a_conn.receiver.sender_ip,a_conn.receiver.sender_port,port,init_sq_number)
        
        send_s.sendto(syn_ack_pack,(a_conn.receiver.sender_ip,a_conn.receiver.sender_port))
        while(True):
            ready_to_read, ready_to_write, in_error = \
                select.select(
                    [recv_s],
                    [],
                    [],
                    1.5)
            
            if ready_to_read :
                ack_pack = recv_s.recvfrom(65535)[0][20:]
                source_port, destination_port, seq_num, ack_num, flags, checksum, receive_window,  urgent_data_pointer = packet.Packet.get_header(ack_pack)

                if destination_port != port:
                    continue
                if not packet.Packet.verify_checksum(syn_ack_pack):
                    continue

                if (flags & (1<<4) ) and (ack_num == init_sq_number + 1 ) :
                    break
            else:
                send_s.sendto(syn_ack_pack,(a_conn.receiver.sender_ip,a_conn.receiver.sender_port))
        
       
        return a_conn


    def close(self):
        try:
            del Conn.binded[self.local_add]
        except KeyError:
            pass
        
        sender = None
        receiver = None
        self.is_close = True

        











class ConnException(Exception):
    pass


def listen(address: str) -> Conn:
    conn = Conn(address)
    conn.listen()
    
    return conn

def accept(conn) -> Conn:
    if conn.is_close:
        raise ConnException('This connection is closed')
    
    return conn.accept()


def dial(address) -> Conn:
    
    conn = Conn()
    conn.dial(address)
    return conn


def send(conn: Conn, data: bytes) -> int:
    if conn.is_close:
        raise ConnException('This connection is closed')
    if not conn.sender:
        raise ConnException('This connection has not used dial or accept ')

    return conn.sender.rdt(data)


def recv(conn: Conn, length: int) -> bytes:
    if conn.is_close:
        raise ConnException('This connection is closed')
    
    if not conn.receiver:
        raise ConnException('This connection has not used dial or accept ')
    
    return conn.receiver.recv(length)


def close(conn: Conn):
    if conn.is_close:
        raise ConnException('This connection is closed')
    conn.close()
