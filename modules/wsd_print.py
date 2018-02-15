#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
import wsd_transfer

from wsd_common import *

import uuid
import argparse
import requests
import lxml.etree as etree

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
"wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
"pri": "http://schemas.microsoft.com/windows/2006/08/wdp/print"}

def WSD_GetPrinterElements(hosted_print_service):

    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submitRequest(hosted_scan_service.ep_ref_addr,
                      "ws-print_getprinterelements.xml",
                      fields,
                      "GET PRINTER ELEMENTS")


if __name__ == "__main__":
    (debug, timeout) = parseCmdLine()
    urn = genUrn()
    tsl = wsd_discovery.WSD_Probe()
    for a in tsl:
        print(a)
        (ti, hss) = wsd_transfer.WSD_Get(a)
        for b in hss:
            if "wprt:PrinterServiceType" in b.types:
                print(b)
                debug = True
                WSD_GetPrinterElements(b)
