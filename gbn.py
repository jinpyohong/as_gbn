# GBN protocol implementation
#

import socket, select, threading, queue, time
import logging
import random, copy

from packet import Seq, srange, make_pkt, get_seqnum, get_type, extract, corrupt

# Parameters of network environment
PER = 0.1           # packet error rate
LOSSRATE = 0.1      # packet loss rate
MEAN_DELAY = 0.2    # mean delay(in seconds) for udt_send

# GBN protocol parameters
TIMEOUT_INTV = 0.5
N = 8       # send window size
assert N < 128, 'N is too big'

# Packet types. Also used event types
DATA = 1
ACK = 2
FIN = 4
FINACK = 6

# Events
Recv_DATA = DATA
Recv_ACK = ACK
Recv_FIN = FIN
Recv_FINACK = FINACK
TIMEOUT = 16
App_SEND = 17
App_CLOSE = 18
CORRUPT = 19

# translate value to name
d = dict(DATA = 1, ACK = 2, FIN = 4, FINACK = 6)
type_name = dict([(v, k) for k, v in d.items()])

d = dict(Recv_DATA = DATA, Recv_ACK = ACK, Recv_FIN = FIN, Recv_FINACK = FINACK,
         TIMEOUT = 16, App_SEND = 17, App_CLOSE = 18, CORRUPT = 19)
event_name = dict([(v, k) for k, v in d.items()])

def show(packet):
    """show symbolic representation of headers"""
    pkt_type = type_name.get(get_type(packet), 'Unknown')
    seq = int(get_seqnum(packet))
    return '%4s %3d %s' %(pkt_type, seq, bytes(packet[4:16]))

# Function simulating unreliable data channel
def udt_send(obj, packet):
    """Unreliable data transfer via connected UDP socket
    to simulate noisy, lossy, and random delayed network envrironment
    """
    # enforce loss
    if random.random() <= LOSSRATE:
        logging.info('udt_send: [dropping] %s', show(packet))
        obj.packets_lost += 1
        obj.packets_sent += 1
        return
    # enforce bit error
    if random.random() <= PER:
        packet = copy.copy(packet)  # deep copy for emulating bit errors
        i = random.randrange(len(packet))
        packet[i] = packet[i] ^ 1  # XOR, enforce bit error
        logging.info('udt_send: [corrupting] %s', show(packet))
        obj.packets_corrupt += 1
    else:
        logging.debug('usd_send: %s', show(packet))
    if MEAN_DELAY > 0.:
        # send after exponential ditributed delay
        time.sleep(random.expovariate(1.0/MEAN_DELAY))
    obj.sock.send(packet)
    obj.packets_sent += 1

def rdt_rcv(obj):
    """Unreliable data reception via connected UDP socket
    """
    packet = obj.sock.recv(2048)
    logging.debug('rdt_rcv:  %s', show(packet))
    obj.packets_rcvd += 1
    return packet

# GBN Sending-side Protocol Entity
class GBNsend(threading.Thread):
    def __init__(self, peer):
        """GBN sending-side

        :param peer: peer hostname
        """

        threading.Thread.__init__(self, name='GBNsend')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 9977))          # GBNsend socket address for simulating UDT channel
        self.sock.connect((peer, 9988))     # just for remembering peer address
        self.down_queue = queue.Queue(N)    # interface between app thread and GBN sender

        self.base = Seq(0)
        self.nextseqnum = Seq(0)
        self.state = 'Wait'
        self.sndpkt = []
        self.expired = False

        # Statistics
        self.packets_sent = self.packets_lost = self.packets_corrupt = 0
        self.packets_rcvd = self.data_requested = 0

    # API - called by sending applications
    def send(self, data):
        """Request to send data
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError('Data should be bytes or bytearray type')
        self.down_queue.put(data)

    def close(self):
        """Request to close the session
        """
        self.down_queue.put(b'')    # empty byte denotes end of data

    # Methods implementing the functions defined in the textbook
    def start_timer(self, interval=TIMEOUT_INTV):
        def handler():              # invoked when timer becomes expired
            self.expired = True

        self.timer = threading.Timer(interval, handler)
        self.timer.start()

    def stop_timer(self):
        self.expired = False
        if self.timer.is_alive():   # Timer thread alive?
            self.timer.cancel()

    # Wrapper methods used in FSM
    def retransmit(self):
        """Retransmit all the packets in the send buffer"""

        # your codes here
        pass

    def send_packet(self, pkt_type, data=b''):
        """Make new packet and send it"""

        # your codes here
        pass

    def handle_ACK(self, packet):
        """Handle arriving ACK packet"""

        # your codes here
        pass

    def get_event(self):
        while True:
            # Check packet arrival
            readable, writable, exceptional = select.select([self.sock], [], [], 0.) # just check ready sockets
            if self.sock in readable:           # something arrives?
                packet = rdt_rcv(self)
                if corrupt(packet):
                    return CORRUPT, packet
                else:
                    event = get_type(packet)
                    return event, packet        # packet types ara also defined as event types

            # Check timeout
            if self.expired:
                self.expired = False
                return TIMEOUT, None

            # Check if application sent something
            if len(self.sndpkt) < N and not self.down_queue.empty():
                data = self.down_queue.get()    # Cannot be blocked!!
                self.data_requested += 1
                if data == b'':                 # App requests to close this session
                    return App_CLOSE, data
                else:
                    return App_SEND, data

            # retry after 0.01 sec to avioid the 'busy form of waiting'
            time.sleep(0.01)

    # GBN sending-side FSM
    def run(self):
        logging.info('GBNsend started')

        while self.state != 'Closed':
            try:
                event, data = self.get_event()
            except socket.error as e:
                logging.error('%s: peer terminated', e)
                self.state = 'Closed'
                break
            rcvpkt = data       # give alias for readiblity
            seqnum = int(get_seqnum(rcvpkt)) if event in type_name else ''
            logging.info('state %s: %s %s in %s:%s',
                self.state, event_name[event], seqnum, self.base, self.nextseqnum)

            if self.state == 'Wait':
                # your codes here

                continue

            if self.state == 'Closing':  # FIN sent, then waiting for FINACK

                # your codes here

                continue
        # end of while loop

        # Closed state:
        logging.info('state=%s: in %s:%s', self.state, self.base, self.nextseqnum)
        logging.info('GBN sender terminated')
        print('Data requested:', self.data_requested)
        print('Packets sent:', self.packets_sent)
        print('\tenforcing lost:', self.packets_lost)
        print('\tenforcing corrupt:', self.packets_corrupt)
        print('Packets rcvd:', self.packets_rcvd)

# GBN Receiving-side Protocol Entity
class GBNrecv(threading.Thread):
    def __init__(self, peer):
        """GBN receiving-side

        :param peer: peer host name
        """

        threading.Thread.__init__(self, name='GBNrecv')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 9988))
        self.sock.connect((peer, 9977))
        self.up_queue = queue.Queue(N)
        self.expected_seqnum = Seq(0)
        self.sndpkt = None
        self.expired = False
        self.sndpkt = make_pkt(self.expected_seqnum, ACK)
        self.state ='Wait'

        # Statistics
        self.packets_sent = self.packets_lost = self.packets_corrupt = 0
        self.packets_rcvd = self.data_delivered = 0

    # GBN API - upper layer calls below methods
    def recv(self): return self.up_queue.get()

    # Methods implementing the function defined in the textbook
    def deliver(self, data):
        self.data_delivered += 1
        self.up_queue.put(data)

    def start_timer(self, interval=TIMEOUT_INTV):
        def handler():
            self.expired = True

        self.timer = threading.Timer(interval, handler)
        self.timer.start()

    def stop_timer(self):
        self.expired = False
        if self.timer.is_alive():
            self.timer.cancel()

    # Wrapper methods used in FSM
    def send_packet(self, pkt_type):
        """Make new packet and send it"""

        #Your codes here
        pass

    def retransmit(self):
        logging.info('Retransmit: %s', get_seqnum(self.sndpkt))
        udt_send(self, self.sndpkt)  # retransmit the previous ACK

    def get_event(self):
        while True:
            readable, writable, exceptional = select.select([self.sock], [], [], 0.)
            if self.sock in readable:
                packet = rdt_rcv(self)
                if corrupt(packet):
                    return CORRUPT, packet
                else:
                    event = get_type(packet)
                    return event, packet
            if self.expired:
                self.expired = False
                return TIMEOUT, None

            time.sleep(0.01)    # retry after 0.01 sec

    def run(self):
        logging.info('GBNrecv started')
        stat_start = None

        while self.state != 'Closed':
            try:
                event, packet = self.get_event()
                if stat_start is None:
                    stat_start = time.time()     # remember start time
            except socket.error as e:
                logging.error('Peer terminated')
                self.state = 'Closed'
                break
            num = '' if type_name.get(event) is None else int(get_seqnum(packet))
            logging.info('state %s: %s %s in %s',
                         self.state, event_name[event], num, self.expected_seqnum)

            if self.state == 'Wait':
                # your codes here

                continue

            # FIN ACKed, but retransmitted packet from GBNsend might be coming.
            if self.state == 'Closing':
                # your codes here

                continue
        # end of while loop

        # Closed state
        elapsed = time.time() - stat_start
        logging.info('state %s: in %s', self.state, self.expected_seqnum)
        logging.info('GBN receiver terminated')

        # Print GBN parametes and statistics
        print('*** GBN parameters ***')
        print('Send window size N:', N)
        print('TIMEOUT_INTV:', TIMEOUT_INTV)
        print('LOSSRATE:', LOSSRATE)
        print('PER:', PER)
        print('MEAN_DELAY:', MEAN_DELAY)

        self.data_delivered -= 1     # don't count termination-signaling packet
        print('\n*** Statistics ***')
        print('Data delivered:', self.data_delivered)
        print('Packets sent:', self.packets_sent)
        print('\tenforcing lost:', self.packets_lost)
        print('\tenforcing corrupt:', self.packets_corrupt)
        print('Packets rcvd:', self.packets_rcvd)
        print('time elapsed: {:.3f} sec'.format(elapsed))
        print('Throughput: {:.2f} data packets/sec'.format(self.data_delivered/elapsed))
