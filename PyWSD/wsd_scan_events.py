#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import http.server
import queue
import threading
import time

from wsd_scan_operations import *

token_map = {}
host_map = {}


def wsd_scanner_elements_change_subscribe(hosted_scan_service, expiration, notify_addr):
    """
        Subscribe to ScannerElementsChange events.

        :param hosted_scan_service: the wsd service to receive event notifications from
        :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
        :param notify_addr: The address to send notifications to.
        :return: False if a fault message is received, True otherwise
    """
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerElementsChangeEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False
    return True


def wsd_scanner_status_summary_subscribe(hosted_scan_service, expiration, notify_addr):
    """
        Subscribe to ScannerStatusSummary events.

        :param hosted_scan_service: the wsd service to receive event notifications from
        :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
        :param notify_addr: The address to send notifications to.
        :return: False if a fault message is received, True otherwise
     """
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusSummaryEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False
    return True


def wsd_scanner_status_condition_subscribe(hosted_scan_service, expiration, notify_addr):
    """
        Subscribe to ScannerStatusCondition events.

        :param hosted_scan_service: the wsd service to receive event notifications from
        :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
        :param notify_addr: The address to send notifications to.
        :return: False if a fault message is received, True otherwise
    """
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False
    return True


def wsd_scanner_status_condition_cleared_subscribe(hosted_scan_service, expiration, notify_addr):
    """
        Subscribe to ScannerStatusConditionCleared events.

        :param hosted_scan_service: the wsd service to receive event notifications from
        :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
        :param notify_addr: The address to send notifications to.
        :return: False if a fault message is received, True otherwise
    """
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionClearedEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False
    return True


def wsd_job_status_subscribe(hosted_scan_service, expiration, notify_addr):
    """
        Subscribe to JobStatus events.

        :param hosted_scan_service: the wsd service to receive event notifications from
        :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
        :param notify_addr: The address to send notifications to.
        :return: False if a fault message is received, True otherwise
    """
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobStatusEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False
    return True


def wsd_job_end_state_subscribe(hosted_scan_service, expiration, notify_addr):
    """
        Subscribe to JobEndState events.

        :param hosted_scan_service: the wsd service to receive event notifications from
        :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
        :param notify_addr: The address to send notifications to.
        :return: False if a fault message is received, True otherwise
    """
    event_uri = "http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobEndStateEvent"
    x = wsd_subscribe(hosted_scan_service, event_uri, expiration, notify_addr)

    if x is False:
        return False
    return True


def wsd_scan_available_event_subscribe(hosted_scan_service, display_str, context_str, expiration, notify_addr):
    """
        Subscribe to ScanAvailable events.

        :param hosted_scan_service: the wsd service to receive event notifications from
        :param display_str: the string to display on the device control panel
        :param context_str: a string internally used to identify the selection of this wsd host as target of the scan
        :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
        :param notify_addr: The address to send notifications to.
        :return: the token needed in CreateScanJob to start a device-initiated scan, \
                or False if a fault message is received instead
    """

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


class HTTPServerWithContext(http.server.HTTPServer):
    def __init__(self, server_address, request_handler_class, context, *args, **kw):
        super().__init__(server_address, request_handler_class, *args, **kw)
        self.context = context


class RequestHandler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        context = self.server.context
        # request_path = self.path
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
        if action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScanAvailableEvent' \
                and context["allow_device_initiated_scans"] is True:
            if debug is True:
                print('##\n## SCAN AVAILABLE EVENT\n##\n')
                print(etree.tostring(x, pretty_print=True, xml_declaration=True))
            client_context = x.find(".//sca:ClientContext", NSMAP).text
            scan_identifier = x.find(".//sca:ScanIdentifier", NSMAP).text
            t = threading.Thread(target=handle_scan_available_event, args=(client_context, scan_identifier))
            t.start()
        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerElementsChangeEvent':

            if debug is True:
                print('##\n## SCANNER ELEMENTS CHANGE EVENT\n##\n')
                print(etree.tostring(x, pretty_print=True, xml_declaration=True))

            sca_config = x.find(".//sca:ScannerConfiguration", NSMAP)
            sca_descr = x.find(".//sca:ScannerDescription", NSMAP)
            std_ticket = x.find(".//sca:DefaultScanTicket", NSMAP)

            description = parse_scan_description(sca_descr)
            configuration = parse_scan_configuration(sca_config)
            std_ticket = parse_scan_ticket(std_ticket)

            context["queues"].sc_descr_q.put(description)
            context["queues"].sc_conf_q.put(configuration)
            context["queues"].sc_ticket_q.put(std_ticket)

        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusSummaryEvent':
            if debug is True:
                print('##\n## SCANNER STATUS SUMMARY EVENT\n##\n')
                print(etree.tostring(x, pretty_print=True, xml_declaration=True))

            state = x.find(".//sca:ScannerState", NSMAP).text
            reasons = []
            q = x.find(".//sca:ScannerStateReasons", NSMAP)
            if q is not None:
                dsr = q.findall(".//sca:ScannerStateReason", NSMAP)
                for sr in dsr:
                    reasons.append(sr.text)
            context["queues"].sc_stat_sum_q.put((state, reasons))

        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionEvent':
            if debug is True:
                print('##\n## SCANNER STATUS CONDITION EVENT\n##\n')
                print(etree.tostring(x, pretty_print=True, xml_declaration=True))

            cond = x.find(".//sca:DeviceCondition", NSMAP)
            cond = parse_scanner_condition(cond)
            context["queues"].sc_cond_q.put(cond)

        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/ScannerStatusConditionClearedEvent':
            if debug is True:
                print('##\n## SCANNER STATUS CONDITION CLEARED EVENT\n##\n')
                print(etree.tostring(x, pretty_print=True, xml_declaration=True))

            cond = x.find(".//sca:DeviceConditionCleared", NSMAP)
            cond_id = int(cond.find(".//sca:ConditionId", NSMAP).text)
            clear_time = cond.find(".//sca:ConditionClearTime", NSMAP).text
            context["queues"].sc_cond_clr_q.put((cond_id, clear_time))

        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobStatusEvent':
            pass  # TODO
        elif action == 'http://schemas.microsoft.com/windows/2006/08/wdp/scan/JobEndStateEvent':
            pass  # TODO


class WSDScannerMonitor:
    """
    A class that abstracts event handling and data querying for a device. Programmer should instantiate this class
    and use its methods to retrieve tickets/configurations/status and more, instead of submitting a wsd request
    directly to the device. This class listens to events and so polling devices is no longer needed.
    """
    def __init__(self, service, listen_addr, port):
        (self.description, self.configuration, self.status, self.std_ticket) = wsd_get_scanner_elements(service)
        self.active_jobs = {}
        for aj in wsd_get_active_jobs(service):
            self.active_jobs[aj.status.id] = wsd_get_job_elements(service, aj.status.id)
        self.job_history = {}
        for ej in wsd_get_job_history(service):
            self.job_history[ej.status.id] = ej

        wsd_scanner_elements_change_subscribe(service, "P0Y0M0DT30H0M0S", listen_addr)
        wsd_scanner_status_summary_subscribe(service, "P0Y0M0DT30H0M0S", listen_addr)
        wsd_scanner_status_condition_subscribe(service, "P0Y0M0DT30H0M0S", listen_addr)
        wsd_scanner_status_condition_cleared_subscribe(service, "P0Y0M0DT30H0M0S", listen_addr)
        wsd_job_status_subscribe(service, "P0Y0M0DT30H0M0S", listen_addr)
        wsd_job_end_state_subscribe(service, "P0Y0M0DT30H0M0S", listen_addr)

        class QueuesSet:
            def __init__(self):
                self.sc_descr_q = queue.Queue()
                self.sc_conf_q = queue.Queue()
                self.sc_ticket_q = queue.Queue()
                self.sc_stat_sum_q = queue.Queue()
                self.sc_cond_q = queue.Queue()
                self.sc_cond_clr_q = queue.Queue()
                self.job_status_q = queue.Queue()
                self.job_ended_q = queue.Queue()

        self.queues = QueuesSet()

        context = {"allow_device_initiated_scans": False,
                   "queues": self.queues}

        server = HTTPServerWithContext(('', port), RequestHandler, context)
        self.listener = threading.Thread(target=server.serve_forever, args=())
        self.listener.start()

    def get_scanner_description(self):
        """
        Updates and returns the current description of the device.

        :return: a valid ScannerDescription instance
        """
        while self.queues.sc_descr_q.empty() is not True:
            self.description = self.queues.sc_descr_q.get()
            self.queues.sc_descr_q.task_done()
        return self.description

    def get_scanner_configuration(self):
        """
        Updates and returns the current configuration of the device.

        :return: a valid ScannerConfiguration instance
        """
        while self.queues.sc_conf_q.empty() is not True:
            self.configuration = self.queues.sc_conf_q.get()
            self.queues.sc_conf_q.task_done()
        return self.configuration

    def get_default_ticket(self):
        """
        Updates and returns the default scan ticket of the device.

        :return: a valid ScanTicket instance
        """
        while self.queues.sc_ticket_q.empty() is not True:
            self.std_ticket = self.queues.sc_ticket_q.get()
            self.queues.sc_ticket_q.task_done()
        return self.std_ticket

    def get_scanner_status(self):
        """
        Updates and returns the current status and conditions of the device.

        :return: a valid ScannerStatus instance
        """
        while self.queues.sc_cond_q.empty() is not True:
            cond = self.queues.sc_cond_q.get()
            self.status.active_conditions[cond.id] = cond
            self.queues.sc_cond_q.task_done()
        while self.queues.sc_cond_clr_q.empty() is not True:
            (c_id, c_time) = self.queues.sc_cond_clr_q.get()
            self.status.conditions_history[c_time] = copy.deepcopy(self.status.active_conditions[c_id])
            del self.status.active_conditions[c_id]
            self.queues.sc_cond_clr_q.task_done()
        while self.queues.sc_stat_sum_q.empty() is not True:
            (self.status.state, self.status.reasons) = self.queues.sc_stat_sum_q.get()
            self.queues.sc_stat_sum_q.task_done()
        return self.status

    # TODO: implement boolean query methods like scanner_status_has_changed and so on


def handle_scan_available_event(client_context, scan_identifier):
    """
    Reply to a ScanAvailable event by issuing the creation of a new scan job.
    Waits for job completion and writes the output to files.

    :param client_context: a string identifying a wsd host selection
    :param scan_identifier: a string identifying the specific scan task to handle
    :return: the number of pages scanned
    """
    host = host_map[client_context]
    dest_token = token_map[client_context]
    ticket = wsd_get_scanner_elements(host).std_ticket
    job = wsd_create_scan_job(host, ticket, scan_identifier, dest_token)
    o = 0
    while wsd_retrieve_image(host, job, "test_%d.jpeg" % o):
        o = o + 1
    return o


def __demo_simple_listener():
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

    server = HTTPServerWithContext(('', 6666), RequestHandler, "context")
    debug = True
    server.serve_forever()


def __demo_monitor():
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    tsl = wsd_discovery.get_devices()
    (ti, hss) = wsd_transfer.wsd_get(list(tsl)[0])
    for b in hss:
        if "wscn:ScannerServiceType" in b.types:
            listen_addr = "http://192.168.1.109:6666/wsd"
            m = WSDScannerMonitor(b, listen_addr, 6666)
            while True:
                time.sleep(2)
                print(m.get_scanner_status())


if __name__ == "__main__":
    __demo_monitor()
