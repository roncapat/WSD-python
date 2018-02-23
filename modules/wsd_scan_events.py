#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import http.server
import threading

from wsd_scan_operations import *

token_map = {}
host_map = {}


def wsd_scanner_elements_change_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerElementsChangeEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False


def wsd_scanner_status_summary_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusSummaryEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False


def wsd_scanner_status_condition_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False


def wsd_scanner_status_condition_cleared_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionClearedEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False


def wsd_job_status_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobStatusEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False


def wsd_job_end_state_subscribe(hosted_scan_service, expiration, notify_addr):
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobEndStateEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False


def wsd_scan_available_event_subscribe(hosted_scan_service, display_str, context_str, expiration, notify_addr):
    fields_map = {"FROM": urn,
                  "TO": hosted_scan_service.ep_ref_addr,
                  "NOTIFY_ADDR": notify_addr,
                  "EXPIRES": expiration,
                  "DISPLAY_STR": display_str,
                  "CONTEXT": context_str}
    x = submit_request(hosted_scan_service.ep_ref_addr, "ws-scan_scanavailableeventsubscribe.xml", fields_map,
                       "SUBSCRIBE")

    if x is False:
        return False

    dest_token = x.find(".//sca:DestinationToken", NSMAP).text
    return dest_token


class RequestHandler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        request_path = self.path
        request_headers = self.headers
        length = int(request_headers["content-length"])

        message = self.rfile.read(length)

        self.protocol_version = "HTTP/1.1"
        self.send_response(202)
        self.send_header("Content-Type", "application/soap+xml")
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()

        x = etree.fromstring(message)
        action = x.find(".//wsa:Action", NSMAP).text
        if action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScanAvailableEvent':
            if debug is True:
                print('##\n## SCAN AVAILABLE EVENT\n##\n')
                print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))
            client_context = x.find(".//sca:ClientContext", NSMAP).text
            scan_identifier = x.find(".//sca:ScanIdentifier", NSMAP).text
            t = threading.Thread(target=handle_scan_available_event, args=(client_context, scan_identifier))
            t.start()
        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerElementsChangeEvent':
            pass
        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusSummaryEvent':
            pass
        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionEvent':
            pass
        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionClearedEvent':
            pass
        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobStatusEvent':
            pass
        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobEndStateEvent':
            pass


def handle_scan_available_event(client_context, scan_identifier):
    host = host_map[client_context]
    dest_token = token_map[client_context]
    ticket = wsd_get_scanner_elements(host).std_ticket
    job = wsd_create_scan_job(host, ticket, scan_identifier, dest_token)
    o = 0
    while wsd_retrieve_image(host, job, "test_%d.jpeg" % o):
        o = o + 1


if __name__ == "__main__":
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    tsl = wsd_discovery.get_devices()
    (ti, hss) = wsd_transfer.wsd_get(list(tsl)[0])
    for b in hss:
        if "wscn:ScannerServiceType" in b.types:
            listen_addr = "http://192.168.1.109:6666/wsd"
            wsd_scanner_elements_change_subscribe(b, "P0Y0M0DT30H0M0S", listen_addr)
            wsd_scanner_status_summary_subscribe(b, "P0Y0M0DT30H0M0S", listen_addr)
            wsd_scanner_status_condition_subscribe(b, "P0Y0M0DT30H0M0S", listen_addr)
            wsd_scanner_status_condition_cleared_subscribe(b, "P0Y0M0DT30H0M0S", listen_addr)
            wsd_job_status_subscribe(b, "P0Y0M0DT30H0M0S", listen_addr)
            wsd_job_end_state_subscribe(b, "P0Y0M0DT30H0M0S", listen_addr)
            dest_token = wsd_scan_available_event_subscribe(b, "PROVA_PYTHON", "python_client", "P0Y0M0DT30H0M0S",
                                                            listen_addr)
            if dest_token is not None:
                token_map["python_client"] = dest_token
                host_map["python_client"] = b
            break
    server = http.server.HTTPServer(('', 6666), RequestHandler)
    debug = True
    server.serve_forever()
