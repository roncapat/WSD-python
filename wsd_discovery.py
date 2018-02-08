#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

from wsd_common import *

import argparse
import struct
import socket
import lxml.etree as etree


class TargetService:
    def __init__(self):
        self.ep_ref_addr = ""
        self.types = []
        self.scopes = []
        self.xaddrs = []
        self.meta_ver = 0
    
    def __str__(self):
        s = ""
        s += "EndPoint reference:   %s\n" % self.ep_ref_addr
        s += "Metadata version:     %d\n" % self.meta_ver
        s += "Implemented Types:    %s\n" % ', '.join(self.types)
        s += "Assigned Scopes:      %s\n" % ', '.join(self.scopes)
        s += "Transport addresses:  %s\n" % ', '.join(self.xaddrs)
        return s
        
    def __eq__(self, other):
        return self.ep_ref_addr == other.ep_ref_addr
    
    def __hash__(self):
        return self.ep_ref_addr.__hash__()


NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
"wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
"wsd": "http://schemas.xmlsoap.org/ws/2005/04/discovery",
"wsdp": "http://schemas.xmlsoap.org/ws/2006/02/devprof",
"wprt": "http://schemas.microsoft.com/windows/2006/08/wdp/print",
"wscn": "http://schemas.microsoft.com/windows/2006/08/wdp/scan",
"i": "http://printer.example.org/2003/imaging"}

def WSD_Probe():
    message = messageFromFile("ws-discovery_probe.xml", FROM=urn)
    multicast_group = ('239.255.255.250', 3702)

    targetServicesList = set()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:
        if debug: print ('##\n## PROBE\n##\n%s' % message)
        sent = sock.sendto(message.encode("UTF-8"), multicast_group)

        while True:
            try:
                data, server = sock.recvfrom(4096)
            except socket.timeout:
                if debug: print ('##\n## TIMEOUT\n##\n')
                break
            else:
                x = etree.fromstring(data)
                if debug: print ('##\n## PROBE MATCH\n## %s\n##\n' % server[0])
                if debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))
                ts = TargetService()
                ts.ep_ref_addr = x.find(".//wsa:Address", NSMAP).text #Optional endpoint fields not implemented yet
                q = x.find(".//wsd:Types", NSMAP)
                if q is not None: ts.types =  q.text.split()
                q = x.find(".//wsd:Scopes", NSMAP)
                if q is not None: ts.scopes = q.text.split()
                q = x.find(".//wsd:XAddrs", NSMAP)
                if q is not None: ts.xaddrs = q.text.split()
                ts.meta_er = int(x.find(".//wsd:MetadataVersion", NSMAP).text)
                targetServicesList.add(ts)
                

        print ("\nFound %d endpoints.\n" % len(targetServicesList))
    finally:
        sock.close()
        return targetServicesList

if __name__ == "__main__":
    (debug, timeout) = parseCmdLine()
    urn = genUrn()
    debug = True
    tsl = WSD_Probe()
    for a in tsl: print(a)
