import logging
# from gbn import GBNrecv
from hong.gbn import GBNrecv # Comment out to use hong's

# Replace the level INFO with DEBUG for debugging or
# or comment out the following line to suppress log messages
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(message)s')

def app_receiver(gr):
    print('app receiver started')
    while True:
        data = gr.recv()
        if data == b'':
            break
        print(data.decode('utf-8'), end='')

gbnrecv = GBNrecv('localhost')
# To change GBN protocol Parameters
# from gbn import N, TIMEOUT_INTV
# N= 16
# TIMEOUT_INTV = 0.4

gbnrecv.start()
app_receiver(gbnrecv)
gbnrecv.join()
