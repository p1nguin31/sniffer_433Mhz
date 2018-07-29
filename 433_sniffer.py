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
import time
from threading import Thread
import traceback

lastTimestampTemperature = {0:0, 1:0, 2:0, 3:0}
lastTimestampTension     = {0:0, 1:0, 2:0, 3:0}
allTemp = [[], [], [], [], []]
allTension = [[], [], [], [], []]
threadCreated = [False, False, False, False, False]

fileName = [r"/home/pi/capteurLastValues0.txt", 
            r"/home/pi/capteurLastValues1.txt",
            r"/home/pi/capteurLastValues2.txt",
            r"/home/pi/capteurLastValues3.txt" ]

def storeValues(tv,  capteur):
    (lastTemp,  lastTension) = tv
    valuesFile = open(fileName[capteur],  'w')
    valuesFile.write("pile:%f temp:%f"  %(lastTension,  lastTemp) )
    valuesFile.close()

def bestValue(tab,  avg):
    goodValue= tab[0]
    bestDelta = abs(goodValue-avg)
    for t in tab:
        delta= abs(t-avg)
        if (delta < bestDelta):
            bestDelta = delta
            goodValue = t
    return goodValue

def collector(capteur):
    try:
        global threadCreated
        global fileName
        if threadCreated[capteur]:
            return
        else:
            threadCreated[capteur] = True
            time.sleep(5)
            threadCreated[capteur] = False
            my_logger.info("waking up to gather all data collected from capteur %d" %capteur)
            filteredTemp = []
            filteredTension = []
            sumTension = 0
            sumTemp = 0
            # let check data received
            for temperature in allTemp[capteur]:
                if (temperature < 100) and ( temperature > -50):
                    # temperature may be kept
                    filteredTemp.append(temperature)
                    sumTemp = sumTemp + temperature
                else:
                    my_logger.warning("Removing out of range value %f for temperature", temperature)
            averageTemp = sumTemp / len(filteredTemp)
            my_logger.debug("received %f acceptable temperature: %s from capteur %d" % (averageTemp,  str(filteredTemp), capteur))

            for tension in allTension[capteur]:
                if (tension > 1) and ( tension < 10):
                    # tension may be kept
                    filteredTension.append(tension)
                    sumTension = sumTension + tension
                else:
                    my_logger.warning("Removing out of range value %f for tension", tension)
            averageTension = sumTension / len(filteredTension)
            my_logger.debug("received %f acceptable tension: %s" % (averageTension,  str(filteredTension)))
            if (len(filteredTemp) > 0) and (len(filteredTension)>0):
                goodTension = bestValue(filteredTension,  averageTension)
                goodTemp = bestValue(filteredTemp,  averageTemp)
                my_logger.info("returning pair (%s, %s) " % (str(goodTemp),  str(goodTension)) )
                storeValues((goodTemp,  goodTension), capteur)
            else:
                return None

    except Exception as e:
            my_logger.error(traceback.format_exc())
            
        
    

def codeStartWith(code,  bitmask):
    return  (code >> (16-3)) == bitmask

def stripCode(code):
    return code & 0x1FFF

def processTemperatureSensor(code):
    global lastTimestampTemperature
    global lastTimestampTension
    global allTemp
    global allTension
    currentTimestamp = time.time()
    capteur = 0
    if code is not None:
        
        if (codeStartWith(code,  0b010)): # capteur 01, tension (0)
            capteur = 1
            if currentTimestamp - lastTimestampTension[capteur] > 5: # new set of temperature
                lastTimestampTension[capteur] = currentTimestamp
                allTension[capteur] = []
            lastTension = stripCode(code)
            lastTension = lastTension/1000.0
            my_logger.info("Received tension %f from sensor 01" %lastTension)
            allTension[capteur].append(lastTension)
            
        elif (codeStartWith(code,  0b011)): # capteur 01, temperature (1)
            capteur = 1
            if currentTimestamp - lastTimestampTemperature[capteur] > 5: # new set of temperature
                lastTimestampTemperature[capteur] = currentTimestamp
                allTemp[capteur] = []
                # init a time of 5 seconds to process all results
            lastTemp = stripCode(code)
            if lastTemp > 0xFFF:
                lastTemp = (lastTemp & 0x1FFF) - 0x2000
            lastTemp = lastTemp/10.0
            my_logger.info("Received temperature %f from sensor 01" %lastTemp)
            allTemp[capteur].append(lastTemp)
        else:
            my_logger.info("Code %d received is not from a remote sensor" % code)
        # create a unique thread to collect all results after some seconds
        t = Thread(target=collector, args=(capteur,))
        t.start()
    

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
      if bits==16:
          # this is a code from my sprinkle system
          # TODO
          pass
      if bits==32:
          # this is coming from my remote temperature sensor
          processTemperatureSensor(code)

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

