#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import wsd_common
import wsd_discovery__operations
import wsd_transfer__operations


def wsd_get_printer_elements(hosted_print_service):
    fields = {"FROM": wsd_common.urn,
              "TO": hosted_print_service.ep_ref_addr}
    wsd_common.submit_request(hosted_print_service.ep_ref_addr,
                              "ws-print__get_printer_elements.xml",
                              fields)


if __name__ == "__main__":
    wsd_common.init()
    (debug, timeout) = wsd_common.parse_cmd_line()
    tsl = wsd_discovery__operations.get_devices()
    for a in tsl:
        print(a)
        (ti, hss) = wsd_transfer__operations.wsd_get(a)
        for b in hss:
            if "wprt:PrinterServiceType" in b.types:
                print(b)
                debug = True
                wsd_get_printer_elements(b)
