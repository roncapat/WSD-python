#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import argparse
import os
import uuid

import lxml.etree as etree
import requests

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
         "wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
         "sca": "http://schemas.microsoft.com/windows/2006/08/wdp/scan"}

headers = {'user-agent': 'WSDAPI', 'content-type': 'application/soap+xml'}
debug = False
timeout = 3
urn = ""

parser = etree.XMLParser(remove_blank_text=True)


def gen_urn():
    """
    Generate a URN. It can be used as device id and/or message id

    :return: a string of the form "urn:uuid:*************************"
    """
    return "urn:uuid:" + str(uuid.uuid4())


def message_from_file(fname, **kwargs):
    """
    Loads an XML template file, minifies it, and fills it with values passed in the kwargs map.

    :param fname: the path of the file to load
    :param kwargs: the dictionary containing the values needed to fill the loaded XML template

    :return: a string representation of the processed xml file
    """
    req = ''.join([l.strip() + ' ' for l in open(fname).readlines()]) \
        .replace('\n', '') \
        .replace('\r', '')
    for k in kwargs:
        req = req.replace('{{' + k + '}}', str(kwargs[k]))
    return req


def parse_cmd_line():
    args_parser = argparse.ArgumentParser(description='WSD Discovery Scanner')
    args_parser.add_argument('-D', action="store_true", default=False, required=False, help='Enable debug')
    args_parser.add_argument('-T', action="store", required=False, type=int, default=2, help='Timeout')

    args = args_parser.parse_args()
    return args.D, args.T


def indent(text):
    s = ""
    for l in text.splitlines():
        s += "\t%s\n" % l
    return s


def abs_path(relpath):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relpath))


def submit_request(addr, xml_template, fields_map, op_name):
    """
    Send a wsd xml/soap request to the specified address, and wait for response.

    :param addr: the address of the wsd service
    :param xml_template: the *name* of the template file to use as payload
    :param fields_map: the dictionary containing the values needed to fill the loaded XML template
    :param op_name: the name of the action, used in debug level output
    :return:
    """
    data = message_from_file(abs_path("../templates/%s" % xml_template), **fields_map)

    if debug:
        r = etree.fromstring(data, parser=parser)
        print('##\n## %s REQUEST\n##\n' % op_name)
        print(etree.tostring(r, pretty_print=True, xml_declaration=True))

    r = requests.post(addr, headers=headers, data=data)

    x = etree.fromstring(r.text)
    if debug:
        print('##\n## %s RESPONSE\n##\n', op_name)
        print(etree.tostring(x, pretty_print=True, xml_declaration=True))
    return x


def wsd_subscribe(hosted_service, event_uri, expiration, notify_addr):
    """
    Subscribe to a certain type of events of a wsd service

    :param hosted_service: the wsd service to receive event notifications from
    :param event_uri: the full URI of the targeted event class. \
                    Those URIs are taken from ws specifications
    :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
    :param notify_addr: The address to send notifications to.
    :return: the reply of the wsd service, or False if a fault message is received instead
    """
    fields_map = {"FROM": urn,
                  "TO": hosted_service.ep_ref_addr,
                  "NOTIFY_ADDR": notify_addr,
                  "EXPIRES": expiration,
                  "EVENT": event_uri}
    x = submit_request(hosted_service.ep_ref_addr, "ws-scan_eventsubscribe.xml", fields_map, "SUBSCRIBE")

    if check_fault(x):
        return False

    return x


def check_fault(xml_soap_tree):
    """
    Check if this soap message represents a Fault or not

    :param xml_soap_tree: an lxml.Etree instance obtained by parsing a wsd service reply
    :return: True if a fault message is detected, False otherwise
    """
    action = xml_soap_tree.find(".//wsa:Action", NSMAP).text
    if action == 'http://schemas.xmlsoap.org/ws/2004/08/addressing/fault':
        code = xml_soap_tree.find(".//soap:Code/soap:Value").text
        subcode = xml_soap_tree.find(".//soap:Subcode/soap:Value").text
        reason = xml_soap_tree.find(".//soap:Reason/soap:Text").text
        detail = xml_soap_tree.find(".//soap:Detail").text
        if debug:
            print('##\n## FAULT\n##\n')
            print("Code: %s\n" % code)
            print("Subcode: %s\n" % subcode)
            print("Reason: %s\n" % reason)
            print("Details: %s\n" % detail)
        return True
    else:
        return False
