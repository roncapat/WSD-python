#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
import wsd_transfer

from wsd_common import *

import uuid
import argparse
import requests
import lxml.etree as etree

def WSD_GetScannerElements(hosted_print_service):
    data = messageFromFile("ws-scan_getscannerelements.xml", FROM=urn, TO=hosted_print_service.ep_ref_addr)
    r = requests.post(hosted_print_service.ep_ref_addr, headers=headers, data=data)

    x = etree.fromstring(r.text)
    if debug: print ('##\n## GET SCANNER ELEMENTS RESPONSE\n##\n')
    if debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))


if __name__ == "__main__":
    (debug, timeout) = parseCmdLine()
    urn = genUrn()
    tsl = wsd_discovery.WSD_Probe()
    for a in tsl:
        print(a)
        (ti, hss) = wsd_transfer.WSD_Get(a)
        for b in hss:
            if "wscn:ScannerServiceType" in b.types:
                print(b)
                debug = True
                WSD_GetScannerElements(b)
