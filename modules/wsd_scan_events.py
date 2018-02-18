#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import http.server

import wsd_discovery
import wsd_transfer
from wsd_common import *


def wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr):
    fields_map = {"FROM": urn,
                  "TO": hosted_scan_service.ep_ref_addr,
                  "NOTIFY_ADDR": notify_addr,
                  "EXPIRES": expiration,
                  "EVENT": event_uri}
    submit_request(hosted_scan_service.ep_ref_addr, "ws-scan_eventsubscribe.xml", fields_map, "SUBSCRIBE")


def wsd_scanner_elements_change_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerElementsChangeEvent"
    wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)


def wsd_scanner_status_summary_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusSummaryEvent"
    wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)


def wsd_scanner_status_condition_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionEvent"
    wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)


def wsd_scanner_status_condition_cleared_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionClearedEvent"
    wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)


def wsd_job_status_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobStatusEvent"
    wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)


def wsd_job_end_state_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobEndStateEvent"
    wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        request_path = self.path
        request_headers = self.headers
        length = int(request_headers["content-length"])

        message = self.rfile.read(length)

        x = etree.fromstring(message)
        print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))

        self.protocol_version = "HTTP/1.1"
        self.send_response(202)
        self.send_header("Content-Type", "application/soap+xml")
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()


if __name__ == "__main__":
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    tsl = wsd_discovery.get_devices()
    (ti, hss) = wsd_transfer.wsd_get(list(tsl)[0])
    for b in hss:
        if "wscn:ScannerServiceType" in b.types:
            wsd_scanner_elements_change_subscribe(b, "P0Y0M0DT30H0M0S", "http://192.168.1.109:6666/wsd")
            wsd_scanner_status_summary_subscribe(b, "P0Y0M0DT30H0M0S", "http://192.168.1.109:6666/wsd")
            wsd_scanner_status_condition_subscribe(b, "P0Y0M0DT30H0M0S", "http://192.168.1.109:6666/wsd")
            wsd_scanner_status_condition_cleared_subscribe(b, "P0Y0M0DT30H0M0S", "http://192.168.1.109:6666/wsd")
            wsd_job_status_subscribe(b, "P0Y0M0DT30H0M0S", "http://192.168.1.109:6666/wsd")
            wsd_job_end_state_subscribe(b, "P0Y0M0DT30H0M0S", "http://192.168.1.109:6666/wsd")
    server = http.server.HTTPServer(('', 6666), RequestHandler)
    server.serve_forever()
