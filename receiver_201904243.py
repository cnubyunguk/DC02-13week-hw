import socket
import os
import sys
import struct
import time
import filecmp
    
def checksum(data):
    ret = 0
    data_len = len(data)
    
    # If the number of data is odd, add one more byte
    if (len(data) % 2):
        data_len += 1
        data += struct.pack('!B', 0)
    
    for i in range(0, data_len, 2):
        ret += int.from_bytes(data[i:i+2], "big")
        
    ret = (ret >> 16) + (ret & 0xFFFF)
    return ~ret & 0xFFFF

if (len(sys.argv) != 3):
    print('please pass host ip address and port number')
    sys.exit()
    
host = sys.argv[1]
port = int(sys.argv[2])

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(0)
    s.settimeout(3)
except socket.error:
    print("failed to create socket")
    sys.exit()
    
req_msg = input("enter your student number: ");
s.sendto(req_msg.encode('utf-8'), (host, port))

file_name = "Received_speech_script.txt"
f = open(file_name, 'wb')

# receive file transfer count
size_msg, _ = s.recvfrom(4096)

my_chksum = checksum(size_msg[:18] + struct.pack('!H', 0) + size_msg[20:])
received_chksum = int.from_bytes(size_msg[18:20], 'big')
if (my_chksum != received_chksum):
    print('[Checksum Error] my checksum: {0} received checksum: {1}'.format(my_chksum, received_chksum))
    sys.exit()

count = int(size_msg[20:].decode('utf-8'))
print("number of receive: {0}".format(count))

# receive file
recv_idx = 0
window_size = 1
init_cnt = count
while(count != 0):
    try:
        data, _ = s.recvfrom(4096)
    except socket.timeout:
        print("raise timeout! Send to server NAK")
        s.sendto("NAK".encode('utf-8'), (host, port))
        continue
        
    my_chksum = checksum(data[1:19] + struct.pack('!H', 0) + data[21:])
    received_chksum = int.from_bytes(data[19:21], 'big')
    if my_chksum != received_chksum:
        print('[Checksum Error] my checksum: {0} received checksum: {1}'.format(my_chksum, received_chksum))
        s.sendto("NAK".encode('utf-8'), (host, port))
        continue
    
    recv_seq = int(data[0])
    if recv_seq != recv_idx:
        print("expected idx: {0} received idx: {1} send to server NAK packet".format(recv_idx, recv_seq))
        s.sendto("NAK".encode('utf-8'), (host, port))
        continue

    f.write(data[21:])
    count -= 1
    
    print("Received frame number: {0}".format(recv_idx))
    print("\treceived packet number {0}".format(init_cnt - count))
    print('\tReceived checksum: {0}'.format(hex(received_chksum)))
    print('\tNew calculated checksum: {0}'.format(hex(my_chksum)))
    
    recv_idx = 0 if recv_idx == window_size else recv_idx + 1
    s.sendto("ACK {0}".format(recv_idx).encode('utf-8'), (host, port))
    print('send ack number: {0}'.format(recv_idx))
    
f.close()
print("file download complete")

origin_file_name = 'speech_script.txt'
copy_file_name = 'Received_speech_script.txt'
print('{0} and {1} is same: {2}'.format(origin_file_name, copy_file_name, filecmp.cmp(origin_file_name, copy_file_name)))
