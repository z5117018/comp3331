from enum import Enum
import socket
from functools import total_ordering

MAX_SEQ = 4294967295

def from_bits(stp_msg):
        seq_num = int(stp_msg[0:32],2)
        ack_num = int(stp_msg[32:64],2)
        payload_len = int(stp_msg[64:96],2)
        checksum = int(stp_msg[96:112],2)
        mss = int(stp_msg[112:144],2)
        mws = int(stp_msg[144:176],2)
        ack = int(stp_msg[176:177],2)
        syn = int(stp_msg[177:178],2)
        fin = int(stp_msg[178:179],2)

        header = Header(seq_num,ack_num,payload_len,checksum,mss,mws,ack,syn,fin)

        if payload_len > 0:
        
            payload = stp_msg[179:].decode('iso-8859-1')
            # print('payload is ', payload)
            return Stp_msg(header,payload)
        else:
            
            return Stp_msg(header)

def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))
class States(Enum):
    CLOSED, SYN_SENT, ESTABLISHED, FIN_WAIT_1, FIN_WAIT_2, TIME_WAIT, LISTEN, SYN_RCVD, CLOSE_WAIT, LAST_ACK = range(0,10)

def bubbleSort(arr):
    n = len(arr)
 
    # Traverse through all array elements
    for i in range(n):
 
        # Last i elements are already in place
        for j in range(0, n-i-1):
 
            # traverse the array from 0 to n-i-1
            # Swap if the element found is greater
            # than the next element
            if arr[j] > arr[j+1] :
                arr[j], arr[j+1] = arr[j+1], arr[j]

class Header:
    def __init__(self, seq_num=0, ack_num=0, payload_len=0, checksum=0, mss=0, mws=0,ack=0, syn=0, fin=0):
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.payload_len = payload_len
        self.checksum = checksum
        self.mss = mss
        self.mws = mws
        self.ack = ack
        self.syn = syn 
        self.fin = fin
    # Convert properties to bits so they can be transferred over socket connection
    def to_bits(self):
        bits = '{0:032b}'.format(self.seq_num)
        bits += '{0:032b}'.format(self.ack_num)
        bits += '{0:032b}'.format(self.payload_len)
        bits += '{0:016b}'.format(self.checksum)
        bits += '{0:32b}'.format(self.mss)
        bits += '{0:32b}'.format(self.mws)
        bits += '{0:01b}'.format(self.ack)
        bits += '{0:01b}'.format(self.syn)
        bits += '{0:01b}'.format(self.fin)
        return bits.encode()
    # Convert from bits to header object when receiving

@total_ordering
class Stp_msg:
    def __init__(self,header,payload=None):
        self.header = header
        self.payload = payload    
    def to_bits(self):
        if self.payload is None:
            return self.header.to_bits()
        else:
            # print('appended is ',self.header.to_bits()+self.payload)
            return self.header.to_bits()+self.payload
    def __lt__(self, other):
        return self.header.seq_num < other.header.seq_num

    def __eq__(self, other):
        return self.header.seq_num == other.header.seq_num

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def checksum(payload):
    s = 0
    # print(len(payload))
    for i in range(0, len(payload)-1, 2):
        # print(i)
        w = ord(payload[i]) + (ord(payload[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff

def bit_sum(payload):
    s = 0
    for i in range(0, len(payload)-1, 2):
        w = ord(payload[i]) + (ord(payload[i+1]) << 8)
        s = carry_around_add(s, w)
    return s & 0xffff
if __name__ =="__main__":
    header = Header(100,100,0,1,1,1)
    # new_header = header.from_bits(header.to_bits())
    client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    client_socket.connect(('127.0.0.1',1200))
    print("sending bits")
    client_socket.send(header.to_bits())
    # print(new_header.seq_num,new_header.ack_num,new_header.ack,new_header.syn,new_header.fin)
# class Headers:

