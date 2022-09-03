#!/usr/bin/env python

# _433.py
# 2015-10-30
# Public Domain

"""
This module provides two classes to use with wireless 433MHz fobs.
The rx class decodes received fob codes. The tx class transmits
fob codes.
"""

import time


if __name__ == "__main__":
   import sys
   import time
   import pigpio
   import _433_TFA_debug
   from logging_iot import my_logger


   RX=20
   TX=21
   
   TX=17
   RX=27

   # define optional callback for received codes.

   def rx_callback(code, bits, gap, t0, t1):
      local_time = time.ctime(time.time())
      my_logger.debug("{} : code={} bits={} (gap={} )".format(local_time, code, bits, gap, t0, t1))
      
      if (bits==36):
          code = code >> 8
          code = code & 0x3FF
          temperature = code / float(10)
          my_logger.info("temperature: %.1f C" % temperature)

   try:
    pi = pigpio.pi() # Connect to local Pi.
    rx=_433_TFA_debug.rx_TFA(pi, gpio=RX, callback=rx_callback, min_bits=8, max_bits=64)
    print("{} : Started").format(time.ctime(time.time()))
    
   
    while True:
       time.sleep(3600)
       my_logger.debug("toujours en vie")


   except KeyboardInterrupt:
       print("Extinction sur interruption clavier")
   except Exception:
       print("Extinction sur exception")

   rx.cancel() # Cancel the receiver.
   pi.stop() # Disconnect from local Pi.

   rx.cancel() # Cancel the receiver.
   pi.stop() # Disconnect from local Pi.

