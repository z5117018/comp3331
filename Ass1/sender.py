import socket
from utils import *
from StpTimer import *
from threading import Timer
import random
from collections import deque
import time
import sys
import _thread

class Sender:
# Drop packets
# • Duplicate packets
# • Create bit errors within packets (a single bit error)
# • Transmits out of order packets
# • Delays packets
# pDrop
# pDuplicate pCorrupt pOrder maxOrder pDelay maxDelay seed
    def __init__(self, receiver_host_ip, receiver_port, file, MWS, 
                MSS, gamma, p_drop, p_duplicate, p_corrupt, p_order, 
                max_order, p_delay, max_delay, seed):
        self.state = States.CLOSED
        # self.seq_num = random.randint(0,MAX_SEQ)
        self.seq_num = 0
        self.last_sent = 0
        self.send_base = 0
        self.receiver_host_ip = receiver_host_ip
        self.receiver_port = receiver_port

        self.file = file
        self.MWS = MWS
        self.MSS = MSS
        self.gamma = gamma
        self.p_drop = p_drop
        self.p_duplicate = p_duplicate
        self.p_corrupt = p_corrupt
        self.p_order = p_order
        self.max_order = max_order # How many packets p_order should wait before sending
        self.p_delay = p_delay
        self.max_delay = 2 # max delay is 2 seconds
        self.seed = seed
        self.held_segment = []
        
        self.payloads = self.create_payloads()
        self.socket = None
        self.timer = StpTimer()
        print("starting seq_num",self.seq_num)
        self.handshake()
        self.final_seq_num = self.seq_num + self.calc_total_payload()


    def init_udp(self):
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.connect((self.receiver_host_ip,self.receiver_port))
        # self.socket.settimeout(self.timer.timeout)
        self.socket.settimeout(0.4)

    def calc_total_payload(self):
        sum = 0
        for p in self.payloads:
            sum += len(p)
        return sum

    def handshake(self): # send SYS, receive SYS+ACK, send ACK
        self.init_udp()
        while True:
            if self.state == States.CLOSED:
                header = Header(self.seq_num,0,0,0,0,0,0,1,0)
                self.stp_send(header=header)
                self.seq_num += 1
                self.state = States.SYN_SENT
            elif self.state == States.SYN_SENT:
                recv = self.stp_rcv(4096)
                print("recv is ",recv.header)
                recv_header = recv.header
                if recv_header.syn and recv_header.ack:
                    # self.ack_num = recv_header.seq_num+1
                    self.state = States.ESTABLISHED
            elif self.state == States.ESTABLISHED:
                header = Header(self.seq_num,0,0,0,0,0,1,0,0)
                self.stp_send(header=header)
                self.seq_num += 1
                recv = self.stp_rcv(4096) # Receive after ack 
                break

    def stp_rcv(self,buf):    
        msg = from_bits(self.socket.recv(buf))
        # self.ack_num = msg.header.seq_num + 1
        return msg


    def stp_send(self,header=None,payload=None, retransmission=False):
        # If only header, user knows what type of header they're sending
        r = random.uniform(0,1)
        if payload is None:
            msg = Stp_msg(header=header)
        # If only payload, we need to wrap this in a header
        else:
            print("Sending last_sent is {} seq_num {}".format(self.last_sent,header.seq_num))
            msg = Stp_msg(header,payload)
            if not retransmission:
                self.seq_num = header.seq_num + len(payload)

                
            if random.uniform(0,1) < self.p_drop:
                print("dropping packet", header.seq_num)
                return -1
            elif random.uniform(0,1) < self.p_duplicate:
                print("***************DUPLICATE*****************")
                self.socket.send(msg.to_bits()) # send once now so it will send again after the conditionals
            elif random.uniform(0,1) < self.p_corrupt:
                print("***************FLIPPING BIT*****************")
                flipped = flip_bit(payload)
                msg = Stp_msg(header,flipped)
            elif r < self.p_order:
                if len(self.held_segment) == 0:
                    print("********************Holding back segment***************", msg.header.seq_num)
                    self.held_segment.append(msg)
                    return 0 
                else:
                    self.socket.send(msg.to_bits())
                    return 1

            #     # next
            elif random.uniform(0,1) < self.p_delay:
                print("***************DELAYING*****************")
                Timer(random.uniform(0,self.max_delay),self.socket.send,[msg.to_bits()])
                return 1
                # time.sleep(random.uniform(0,self.max_delay))
        self.socket.send(msg.to_bits())
        return 1
        
    def create_payloads(self):
        file = open(self.file,mode='rb')
        contents = file.read()
        file.close()
        print("number of things to send: ",len(list(chunkstring(contents,self.MSS))))
        return deque(list(chunkstring(contents,self.MSS)))

    def stp_timer_send(self,header=None,payload=None, retransmission=False):
        print("RESENDING ", header.seq_num)
        r = random.uniform(0,1)
        if payload is None:
            msg = Stp_msg(header=header)
        # If only payload, we need to wrap this in a header
        else:
            # print("Sending last_sent is {} seq_num {}".format(self.last_sent,header.seq_num))
            msg = Stp_msg(header,payload)
            if not retransmission:
                self.seq_num = header.seq_num + len(payload)

                
            # if r < self.p_drop:
            #     print("dropping packet", header.seq_num)
            #     return -1
            # elif r < self.p_duplicate:
            #     self.socket.send(msg.to_bits()) # send once now so it will send again after the conditionals
            # elif r < self.p_corrupt:
            #     flipped = flip_bit(payload)
            #     msg = Stp_msg(header,flipped)
            # elif r < self.p_order:
            # # if r < self.p_order and len(self.held_segment) == 0:
            #     print("Holding back segment", msg.header.seq_num)
            #     self.held_segment.append(msg)
            #     return -1
                

            #     # next
            # elif r < self.p_delay:
            #     time.sleep(random.uniform(0,self.max_delay))
        self.socket.send(msg.to_bits())
        return 1

    def stp_close(self):
        self.socket.settimeout(2*self.timer.timeout)
        while True:
            if self.state == States.ESTABLISHED:
                header = Header(self.seq_num,0,0,0,0,0,0,0,1)
                self.stp_send(header=header)
                self.seq_num += 1
                self.state = States.FIN_WAIT_1
            elif self.state == States.FIN_WAIT_1:
                try:
                    recv = self.stp_rcv(4096) # Receive after ack 
                    print("RECEVIED ACK FOR CLOSE")
                    if recv.header.ack and recv.header.ack_num == self.seq_num:
                        self.state = States.CLOSED
                except socket.timeout:
                    continue
            elif self.state == States.CLOSED:
                print("CLOSED CONNECTION END")
                break


    def send_payloads(self):
        num_duplicates = 0
        size = 0
        send_base_seq_num = self.seq_num
        held_count = 0

        while(True):
            print("seq num is {} final is {}".format(self.seq_num,self.final_seq_num))

            # If the packet is re-ordered, this means another packet has to replace it and still increment last sent
            if (self.last_sent - self.send_base < self.MWS and self.send_base < len(self.payloads)):
                if (held_count == self.max_order):
                    msg = self.held_segment.pop()
                #     _thread.start_new_thread(self.stp_send, (msg.header, msg.payload, True) )    
                    held_count = 0
                    self.stp_send(msg.header,msg.payload,True)
                    print("**************released held back segment**********************",msg.header.seq_num)
                    continue       
                
                if self.last_sent >= len(self.payloads):
                    print("There are packets that need to be resent even though last_sent = len(payloads)")
                    payload = self.payloads[self.send_base]
                    header = Header(send_base_seq_num,0,len(payload),checksum(payload.decode('iso-8859-1')))
                else:
                    print("last sent is {} and send_base is {}".format(self.last_sent,send_base_seq_num))
                    payload = self.payloads[self.last_sent]
                    header = Header(self.seq_num,0,len(payload),checksum(payload.decode('iso-8859-1')))
                
                # _thread.start_new_thread(self.stp_send, (header, payload, False) )
                res = self.stp_send(header,payload,False)
                
                if (self.timer.start_timer == False):
                    # print ("setting timer for ", header.seq_num, "with base seq num ", send_base_seq_num)
                    payload = self.payloads[self.send_base]
                    header = Header(send_base_seq_num,0,len(payload),checksum(payload.decode('iso-8859-1')))
                    self.timer.start_timer = True
                    send_time = int(round(time.time()*1000))  
                    print("***********************settting timer**********************", send_base_seq_num,self.timer.timeout)
                    t = Timer(2,self.stp_timer_send,[header,payload,True])
                    t.start()
                    

                # if res == -1: # if its a hold back then skip
                    # continue
                # self.stp_send(header,payload)
                # print("incrementing")
                
                self.last_sent += 1
                if res == -1:
                    continue
                elif res != 0 and len(self.held_segment) > 0:
                    held_count += 1
                # print("sending seq_num",self.seq_num-99, "held", held_count)
            
            # self.seq_num += len(payload)
            # try:
            # reply,address = self.socket.recvfrom(self.receiver_port)
            # Will wait for data so if packet drops, continue 
            
            try:
                reply = self.socket.recv(4096)
                # reply_time = int(round(time.time()*1000))
                # self.timer.start_timer = False
                # rtt = (reply_time - send_time)
                # self.socket.settimeout(self.timer.calc_timeout(rtt,False))
                # print("timer is ",self.timer.timeout)
                header = from_bits(reply).header
                print("header ack num is {}".format(header.ack_num))
                    # finish when the ack equals final sequence number
                if (header.ack_num > send_base_seq_num):
                    print("Cancelling timer new send base seq num ",send_base_seq_num)
                    self.send_base += int((header.ack_num - send_base_seq_num)/self.MSS)
                    send_base_seq_num = header.ack_num
                    # Clear up retransmission timer
                    
                    t.cancel()
                    self.timer.start_timer = False
                    recv_time = int(round(time.time()*1000))  
                    self.timer.calc_timeout(recv_time-send_time)
                    if (header.ack_num == self.final_seq_num):
                        print("closing!")
                        self.stp_close()
                        break
                    # else:
                        # self.timer.start_timer = True
                        # send_time = int(round(time.time()*1000))   
                    #                 if (there are currently any not-yet-acknowledged segments)
#                     start timer 
#                 }
                    # self.send_base = header.ack_num
                    # rtt = (reply_time - send_time)
                    # self.timer.calc_timeout(rtt)
                    # self.last_acked += 1 # we have one acknowledged 
                    # NEED TO SET SEND_BASE 
                    # self.send_base += len(payload)
                    # if(self.sent_unacked):
                        # send_time = int(round(time.time()*1000))
                        # self.start_timer = True
                        # start timer
                else:
                    num_duplicates += 1
                    if (num_duplicates == 3):
                        print("fast retransmission")
                        payload = self.payloads[self.send_base]
                        header = Header(send_base_seq_num,0,len(payload),checksum(payload.decode('iso-8859-1')))
                        self.stp_send(header,payload,True)
                        # _thread.start_new_thread(self.stp_send, (header, payload, True) )
                        num_duplicates = 0

            except socket.timeout:
                continue
                # print("timeed out, retransmitting seq_num {}".format(send_base_seq_num))
                # payload = self.payloads[self.send_base]
                # header = Header(send_base_seq_num,0,len(payload),checksum(payload.decode('iso-8859-1')))
                # send_time = int(round(time.time()*1000))
                # _thread.start_new_thread(self.stp_send, (header, payload, True) )
                # send_time = int(round(time.time()*1000))
                
                        # retransmit not-yet-acknowledged segment with
                            # smallest sequence number 
                        # start timer
                        # break
            
    

    # loop (forever) { 
#     switch(event)
#         event: data received from application above
#             create TCP segment with sequence number NextSeqNum 
#             if (timer currently not running)
#                 start timer
#             pass segment to IP NextSeqNum=NextSeqNum+length(data) 
#             break;

#         event: timer timeout
#             retransmit not-yet-acknowledged segment with
#                 smallest sequence number 
#             start timer
#             break;

#         event: ACK received, with ACK field value of y 
#             if (y > SendBase) {
#                 SendBase=y
#                 if (there are currently any not-yet-acknowledged segments)
#                     start timer 
#                 }
#             else { /* a duplicate ACK for already ACKed
#                 segment */
#                 increment number of duplicate ACKs
#                     received for y
#                 if (number of duplicate ACKS received for y==3)
#                     /* TCP fast retransmit */
#                     resend segment with sequence number y
#                 }
#             break;
# }

if __name__ == "__main__":
    sender = Sender('127.0.0.1',11200,'test0.pdf',8,99,4,0.3,0.5,0.5,0.5,5,0.5,2,1000)
    sender.send_payloads()
    