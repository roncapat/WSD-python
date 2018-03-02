#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import wsd_discovery__operations
import wsd_transfer__operations

from wsd_common import *


def wsd_get_printer_elements(hosted_print_service):
    fields = {"FROM": urn,
              "TO": hosted_print_service.ep_ref_addr}
    submit_request(hosted_print_service.ep_ref_addr,
                   "ws-print__get_printer_elements.xml",
                   fields)


if __name__ == "__main__":
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    tsl = wsd_discovery__operations.get_devices()
    for a in tsl:
        print(a)
        (ti, hss) = wsd_transfer__operations.wsd_get(a)
        for b in hss:
            if "wprt:PrinterServiceType" in b.types:
                print(b)
                debug = True
                wsd_get_printer_elements(b)
