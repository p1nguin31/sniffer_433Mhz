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
import json

lastTimestampTemperature = {0:0, 1:0, 2:0, 3:0}
lastTimestampTension     = {0:0, 1:0, 2:0, 3:0}
allTemp = [[], [], [], [], []]
allTension = [[], [], [], [], []]
threadCreated = [False, False, False, False, False]

fileName = [r"/home/pi/capteurLastValues0.txt", 
            r"/home/pi/capteurLastValues1.txt",
            r"/home/pi/capteurLastValues2.txt",
            r"/home/pi/capteurLastValues3.txt" ]

fileNameArrosage = r"/home/pi/arrosageStatus.txt"

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
            my_logger.debug("received %f acceptable temperature: %s from capteur %02d" % (averageTemp,  str(filteredTemp), capteur))

            for tension in allTension[capteur]:
                if (tension > 1) and ( tension < 10):
                    # tension may be kept
                    filteredTension.append(tension)
                    sumTension = sumTension + tension
                else:
                    my_logger.warning("Removing out of range value %f for tension", tension)
            averageTension = sumTension / len(filteredTension)
            my_logger.debug("received %f acceptable tension: %s from capteur %02d" % (averageTension,  str(filteredTension), capteur))
            if (len(filteredTemp) > 0) and (len(filteredTension)>0):
                goodTension = bestValue(filteredTension,  averageTension)
                goodTemp = bestValue(filteredTemp,  averageTemp)
                my_logger.info("returning pair (%s, %s) from capteur %02d" % (str(goodTemp),  str(goodTension), capteur) )
                storeValues((goodTemp,  goodTension), capteur)
            else:
                return None

    except Exception as e:
            my_logger.error(traceback.format_exc())
            
        
    

def codeStartWith(code,  bitmask):
    return  (code >> (16-3)) == bitmask

def stripCode(code):
    return code & 0x1FFF

def getNoise(code):
    return (code & 0xFFFF0000) >> 16

def processTemperatureSensor(code):
    global lastTimestampTemperature
    global lastTimestampTension
    global allTemp
    global allTension
    currentTimestamp = time.time()
    capteur = 0
    if code is not None:
        noise = getNoise(code)
        code = code & 0xFFFF
        capteur = code >> 14        
        
        #my_logger.info("sensor %02d" %(capteur))
        if (codeStartWith(code,  (capteur << 1))): # capteur xx, tension (0). le 'noise' est sur les 16 bits hauts
            if currentTimestamp - lastTimestampTension[capteur] > 5: # new set of temperature
                lastTimestampTension[capteur] = currentTimestamp
                allTension[capteur] = []
            lastTension = stripCode(code)
            lastTension = lastTension/1000.0
            my_logger.info("Received tension %f from sensor %02d" %(lastTension, capteur))
            my_logger.info("Received noise %f from sensor %02d" %(noise, capteur))
            allTension[capteur].append(lastTension)
            
        elif (codeStartWith(code,  (capteur << 1) + 1 )): # capteur xx, temperature (1)
            if currentTimestamp - lastTimestampTemperature[capteur] > 5: # new set of temperature
                lastTimestampTemperature[capteur] = currentTimestamp
                allTemp[capteur] = []
                # init a time of 5 seconds to process all results
            lastTemp = stripCode(code)
            if lastTemp > 0xFFF:
                lastTemp = (lastTemp & 0x1FFF) - 0x2000
            lastTemp = lastTemp/10.0
            my_logger.info("Received temperature %f from sensor %02d" %(lastTemp, capteur))
            allTemp[capteur].append(lastTemp)
        else:
            my_logger.info("Code %d received is not from a remote sensor" % code)
        # create a unique thread to collect all results after some seconds
        t = Thread(target=collector, args=(capteur,))
        t.start()

def processArrosageFeedback(code):
    if code == 0xFFFF:
        code = 0
    initDone = (code & 1) == 1
    code = code >> 1
    arrosageStatus = (code & 1) == 1
    code = code >> 1
    duree = code

    my_logger.info("initDone : %s - arrosage en cours : %s - duree : %d" % (str(initDone), str(arrosageStatus), duree))
    
    stringToBeSaved = json.dumps({"initDone" : initDone, "arrosageStatus": arrosageStatus, "duree": duree })
    valuesFile = open(fileNameArrosage,  'w')
    valuesFile.write(stringToBeSaved)
    valuesFile.close()

    
    if initDone and (not arrosageStatus):
        my_logger.info("Debut Arrosage dans %d minutes" % (duree + 1) )
    if initDone and arrosageStatus:
        my_logger.info("Arrosage en cours pendant encore %d minutes" % (duree +1) )
    if (not initDone) and arrosageStatus:
        my_logger.info("Arrosage manuel en cours")
    if (not initDone) and (not arrosageStatus):
        my_logger.info("Aucune programmation en cours" )

def processArrosageRequest(code):
    crc_received = code & 0xFF
    value = code >> 8
    # check CRC
    crc_computed = (value & 0xFF) + (value >> 8) & 0xFF
    my_logger.debug("crc received: %.2X - crc computed : % .2X - value received is %d" % (crc_received, crc_computed, value))
    if (crc_computed != crc_received):
        my_logger.warning("CRC mismatch")
    else:
        my_logger.info("received command to start sprinkling in %d minutes" % value)

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
          processArrosageFeedback(code)
      if bits==24:
          # this is a code to my sprinkle system
          processArrosageRequest(code)
          pass
      if bits==32:
          # this is coming from my remote temperature sensor
          if (code >> 16) == 0:
              processTemperatureSensor(code)
          else:
              processTemperatureSensor(code) # pour mise au point de la detection du 220 V
              my_logger.info("Code errone recu : %d" % code)

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

