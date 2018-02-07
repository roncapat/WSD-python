#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
import wsd_get

from wsd_discovery import _debug
from wsd_get import _urn

import uuid
import argparse
import requests
import lxml.etree as etree

headers={'user-agent': 'WSDAPI', 'content-type': 'application/soap+xml'}

def WSD_GetPrinterElements(hosted_print_service):
    data = wsd_get.messageFromFile("ws-print_getprinterelements.xml", FROM=_urn, TO=hosted_print_service.ep_ref_addr)
    r = requests.post(hosted_print_service.ep_ref_addr, headers=headers, data=data)

    x = etree.fromstring(r.text)
    if _debug: print ('##\n## GET PRINTER ELEMENTS RESPONSE\n##\n')
    if _debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))


if __name__ == "__main__":
    wsd_discovery.parseCmdLine()
    wsd_get.genUrn()
    tsl = wsd_discovery.WSD_Probe()
    for a in tsl:
        #print(a)
        (ti, hss) = wsd_get.WSD_Get(a)
        #print(ti)
        for b in hss:
            if "wprt:PrinterServiceType" in b.types:
                _debug = True
                WSD_GetPrinterElements(b)
