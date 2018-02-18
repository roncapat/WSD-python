#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import wsd_discovery
import wsd_transfer

from wsd_common import *

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
         "wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
         "pri": "http://schemas.microsoft.com/windows/2006/08/wdp/print"}


def wsd_get_printer_elements(hosted_print_service):
    fields = {"FROM": urn,
              "TO": hosted_print_service.ep_ref_addr}
    submit_request(hosted_print_service.ep_ref_addr,
                   "ws-print_getprinterelements.xml",
                   fields,
                   "GET PRINTER ELEMENTS")


if __name__ == "__main__":
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    tsl = wsd_discovery.get_devices()
    for a in tsl:
        print(a)
        (ti, hss) = wsd_transfer.wsd_get(a)
        for b in hss:
            if "wprt:PrinterServiceType" in b.types:
                print(b)
                debug = True
                wsd_get_printer_elements(b)
