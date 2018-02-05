#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import argparse
import struct
import socket
import lxml.etree as etree

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
"wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
"wsd": "http://schemas.xmlsoap.org/ws/2005/04/discovery",
"wsdp": "http://schemas.xmlsoap.org/ws/2006/02/devprof",
"wprt": "http://schemas.microsoft.com/windows/2006/08/wdp/print",
"wscn": "http://schemas.microsoft.com/windows/2006/08/wdp/scan",
"i": "http://printer.example.org/2003/imaging"}

def messageFromFile(fname):
    return ''.join(open(fname).readlines())

parser = argparse.ArgumentParser(description='WSD Discovery Scanner')
parser.add_argument('-D', action="store_true", default=False, required=False, help='Enable debug')
parser.add_argument('-T', action="store", required=False, type=int, default=2, help='Timeout')

args = parser.parse_args()
_debug, _timeout = args.D, args.T

message = messageFromFile("wsd_discovery-probe_generic-device.xml")
multicast_group = ('239.255.255.250', 3702)

class TargetService:
    def __init__(self):
        self.ep_ref_addr = ""
        self.types = []
        self.scopes = []
        self.xaddrs = []
    
    def __str__(self):
        s = ""
        s += "EndPoint Reference Address:\n\t%s\n" % self.ep_ref_addr
        if self.types:
            s += "Implemented Types:\n"
            for t in self.types:
                s+="\t%s\n" % t
        if self.scopes:
            s += "Assigned Scopes:\n"
            for t in self.scopes:
                s+="\t%s\n" % t
        if self.types:
            s += "Transport addresses:\n"
            for t in self.xaddrs:
                s+="\t%s\n" % t
        return s
        
    def __eq__(self, other):
        return self.ep_ref_addr == other.ep_ref_addr
    
    def __hash__(self):
        return self.ep_ref_addr.__hash__()

targetServicesList = set()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(_timeout)
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:
    if _debug: print ('##\n## PROBE\n##\n%s' % message)
    sent = sock.sendto(message.encode("UTF-8"), multicast_group)

    while True:
        try:
            data, server = sock.recvfrom(4096)
        except socket.timeout:
            if _debug: print ('##\n## TIMEOUT\n##\n')
            break
        else:
            x = etree.fromstring(data)
            if _debug: print ('##\n## PROBE MATCH\n## %s\n##\n' % server[0])
            if _debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))
            ts = TargetService()
            ts.ep_ref_addr = x.find(".//wsa:Address", NSMAP).text
            q = x.find(".//wsd:Types", NSMAP)
            if q is not None: ts.types =  q.text.split()
            q = x.find(".//wsd:Scopes", NSMAP)
            if q is not None: ts.scopes = q.text.split()
            q = x.find(".//wsd:XAddrs", NSMAP)
            if q is not None: ts.xaddrs = q.text.split()
            targetServicesList.add(ts)

    print ("\nFound %d endpoints.\n" % len(targetServicesList))
    for a in targetServicesList: print(a)

finally:
    sock.close()
