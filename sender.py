import logging
from urllib.request import urlopen

# from gbn import GBNsend
from hong.gbn import GBNsend  # Comment out to use hong's

# Replace the level INFO with DEBUG for debugging
# or comment out the following line to suppress log messages
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(message)s')

# Short text for debugging
def textlines(lines):
    for i in range(lines):
        yield '%05d abcdefghijklmnopqrstuvwxyz\n' % i

def app_sender(gs):
    print('app sender started')
    for line in textlines(16):
        gs.send(line.encode('utf-8'))
    gs.close()
    print('app sender terminated')

gbnsend = GBNsend('localhost')
# To change GBN protocol Parameters
# from gbn import N, TIMEOUT_INTV
# N= 16
# TIMEOUT_INTV = 0.4

gbnsend.start()
app_sender(gbnsend)
gbnsend.join()