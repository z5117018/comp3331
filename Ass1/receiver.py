import socket as s 
from utils import *
import random
from collections import deque
import sys
# from itertools import *
class Receiver:
    def __init__(self,receiver_port,file_r):
        self.state = States.CLOSED
        # self.seq_num = random.randint(0,120000)
        # self.seq_num = random.randint(0,MAX_SEQ)
        self.ack_num = None

        self.receiver_port = receiver_port
        self.file_r = file_r

        self.msg_buffer = deque([])

        self.socket = None
        self.udp_listen()

    def udp_listen(self):
        self.socket = s.socket(s.AF_INET, s.SOCK_DGRAM)  
        self.socket.bind(('127.0.0.1', self.receiver_port))

        # Accept unencoded header and payload
    def stp_send(self,address,header=None,payload=None):
        # If only header, user knows what type of header they're sending
        if payload is None:
            msg = Stp_msg(header=header)
        # If only payload, we need to wrap this in a header
        else:
            # increment
            # self.seq_num += len(payload.encode('utf-8'))
            header = Header(0,self.ack_num,0,0,0)
            msg = Stp_msg(header,payload)
            
        self.socket.sendto(msg.to_bits(),address)
    

    def stp_rcv(self,buf):    
        msg = self.socket.recv(buf)
        header = from_bits(msg.header)
        payload = msg.payload
        self.ack_num = header.seq_num + 1

    def stp_write(self,message,f):

        if len(self.msg_buffer) > 0:
            # print("herererere")
            # sys.exit()
            next_seq = self.msg_buffer[0].header.seq_num
            while self.msg_buffer:
                print("INSIDE WhiLE LOOP SEQ NUM IS ",next_seq)
                # break
                msg = self.msg_buffer[0]
                if (next_seq == msg.header.seq_num):
                    
                    payload = self.msg_buffer.popleft().payload
                    f.write(payload)
                    self.ack_num += msg.header.payload_len   
                    next_seq = msg.header.seq_num + msg.header.payload_len
                else:
                    break           
            sys.exit()  
            # for msg in self.msg_buffer:
            #     if (next_seq == msg.header.seq_num):
            #         payload = self.msg_buffer.popleft().payload
            #         f.write(payload)
            #         self.ack_num += msg.header.payload_len
            #     next_seq = msg.header.seq_num + msg.header.payload_len
        else:
            print(message.payload)
            f.write(message.payload)
            self.ack_num += message.header.payload_len
            # print("new acknum",self.ack_num)
        

if __name__ == "__main__":    
    f = open("copy21.pdf","w+") 
    receiver = Receiver(11200,'file')
    # arr = []
    size = 0
    while True:
        message, address = receiver.socket.recvfrom(4096)
        # size = 311 - sys.getsizeof(message)
        # print(size)
        # if(size == 0 or size == 99):
        #     continue
        # else:
        #     break
        size += 1
        if message is not None:
            recv_header = from_bits(message).header
            
            if recv_header.syn:
                
                # receiver.seq_num += 1
                receiver.ack_num = recv_header.seq_num + 1
                header = Header(0,receiver.ack_num,0,0,0,0,1,1,0)
                print("setting acknum as ",receiver.ack_num)
            elif recv_header.ack:
                # connection established
                # receiver.seq_num += 1
                receiver.ack_num = recv_header.seq_num + 1
                header = Header(0,receiver.ack_num,0,0)
                print("connection established",receiver.ack_num)
            else:
                message = from_bits(message)
                
                # print("message leng", message.header.payload_len)
                
                # arr.append(len(message.payload))
                # print(arr)
                # print([(y-x)%99 for x,y in zip(sorted(arr),sorted(arr[1:]))])
                if message.header.seq_num == receiver.ack_num:
                    # self.acknum += message.header.payload_len
                    # print("here")
                    # print(message)
                    receiver.stp_write(message,f)
                    # Write all payloads 
                else:
                    # print("in else")
                    # print(message)
                    receiver.msg_buffer.append(message)
                    # print("len is",len(receiver.msg_buffer))
                    # Don't increment acknum
                receiver.ack_num += message.header.payload_len
                print("seq_num: {} ack_num: {}".format(message.header.seq_num,receiver.ack_num))
                header = Header(0,receiver.ack_num,0,0,0,0,1,0,0)
                print(size)
                # if (message is not None):
                    # f = open("copy1.pdf","w+") 
                    # f.write(from_bits(message).payload.decode('iso-8859-1'))
            receiver.stp_send(address=address,header=header)
    f.close()
# (self, seq_num=0, ack_num=0, payload_len=0, checksum=0, mss=0, mws=0,ack=0, syn=0, fin=0):