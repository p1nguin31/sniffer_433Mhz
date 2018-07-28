#!/usr/bin/env python

# _433.py
# 2015-10-30
# Public Domain

"""
This module provides two classes to use with wireless 433MHz fobs.
The rx class decodes received fob codes. The tx class transmits
fob codes.
"""

from logging_iot import my_logger



if __name__ == "__main__":

   import sys
   import time
   import pigpio
   import _433


   RX=20
   TX=21
   
   TX=17
   RX=27

   # define optional callback for received codes.

   def rx_callback(code, bits, gap, t0, t1):
      my_logger.info("code={} bits={} (gap={} t0={} t1={})".format(code, bits, gap, t0, t1))

   try:
      pi = pigpio.pi() # Connect to local Pi.
      rx=_433.rx(pi, gpio=RX, callback=rx_callback)
   
      while True:
          time.sleep(3600)
          my_logger.debug("toujours en vie")
   
   except KeyboardInterrupt:
       my_logger.info("Extinction sur interruption clavier")
   except Exception:
       my_logger.warn("Extinction sur exception")

   rx.cancel() # Cancel the receiver.
   pi.stop() # Disconnect from local Pi.

