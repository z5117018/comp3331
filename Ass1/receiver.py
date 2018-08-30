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
        self.ack_num = 0

        self.recv_base = self.ack_num

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
            print("INSIDE WhiLE LOOP SEQ NUM IS {} ACK is {}".format(message.header.seq_num,self.ack_num))
            # Need to write current message and then loop through buffer
            next_seq = message.header.seq_num + message.header.payload_len
            f.write(message.payload)
            self.ack_num += message.header.payload_len
            while self.msg_buffer:
                
                # break
                msg = self.msg_buffer[0]
                if (next_seq == msg.header.seq_num):
                    print("inside if statement, message header sequence number is {}".format(msg.header.seq_num))
                    payload = self.msg_buffer.popleft().payload
                    f.write(payload)
                    self.ack_num += msg.header.payload_len   
                    next_seq = msg.header.seq_num + msg.header.payload_len
                else:
                    # self.recv_base = next_seq
                    break           

        else:
            # print(message.payload)
            f.write(message.payload)
            self.ack_num += message.header.payload_len
            # print("new acknum",self.ack_num)
        

if __name__ == "__main__":    
    f = open("copy22.pdf","w+") 
    receiver = Receiver(11200,'file')
    while True:
        message, address = receiver.socket.recvfrom(4096)

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
                print("Received seqnum is {} and my ack num is {}".format(message.header.seq_num,receiver.ack_num))
                if message.header.seq_num == receiver.ack_num:
                    receiver.stp_write(message,f)
                    header = Header(0,receiver.ack_num,0,0,0,0,1,0,0)
                elif message.header.seq_num > receiver.ack_num: # ack num is the most recently acknowledged seq num. ignore if seq_num < ack_num as this is a received retransmission
                    print("appending to buffer")
                    receiver.msg_buffer.append(message)
                    bubbleSort(receiver.msg_buffer)
                    header = Header(0,receiver.ack_num,0,0,0,0,1,0,0)

                
            receiver.stp_send(address=address,header=header)
    f.close()
# (self, seq_num=0, ack_num=0, payload_len=0, checksum=0, mss=0, mws=0,ack=0, syn=0, fin=0):