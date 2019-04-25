#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import argparse
import datetime
import random
import time
import os
import typing
import uuid

import lxml.etree as etree
import requests
from PyWSD import wsd_globals

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
         "mex": "http://schemas.xmlsoap.org/ws/2004/09/mex",
         "wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
         "wsd": "http://schemas.xmlsoap.org/ws/2005/04/discovery",
         "wse": "http://schemas.xmlsoap.org/ws/2004/08/eventing",
         "wsdp": "http://schemas.xmlsoap.org/ws/2006/02/devprof",
         "i": "http://printer.example.org/2003/imaging",
         "pri": "http://schemas.microsoft.com/windows/2006/08/wdp/print",
         "sca": "http://schemas.microsoft.com/windows/2006/08/wdp/scan",
         "pnpx": "http://schemas.microsoft.com/windows/pnpx/2005/10",
         "df": "http://schemas.microsoft.com/windows/2008/09/devicefoundation"}

headers = {'user-agent': 'WSDAPI', 'content-type': 'application/soap+xml'}
log_path = "../log"

parser = etree.XMLParser(remove_blank_text=True)


def gen_urn() -> str:
    """
    Generate a URN. It can be used as device id and/or message id

    :return: a string of the form "urn:uuid:*************************"
    :rtype: str
    """
    return "urn:uuid:" + str(uuid.uuid4())


# TODO: replace dumb text substitution with xml tree manipulation
def message_from_file(fname: str,
                      **kwargs) \
        -> str:
    """
    Loads an XML template file, minifies it, and fills it with values passed in the kwargs map.

    :param fname: the path of the file to load
    :type fname: str
    :param kwargs: the dictionary containing the values needed to fill the loaded XML template
    :return: a string representation of the processed xml file
    :rtype: str
    """
    req = ''.join([l.strip() + ' ' for l in open(fname).readlines()]) \
        .replace('\n', '') \
        .replace('\r', '')
    for k in kwargs:
        req = req.replace('{{' + k + '}}', str(kwargs[k]))
    req = req.replace('{{MSG_ID}}', gen_urn())
    return req


def indent(text: str) -> str:
    """
    Indent (multiline) text with tabs
    :param text: the text to indent
    :type text: str
    :return: the indented text
    :rtype: str
    """
    s = ""
    for l in text.splitlines():
        s += "\t%s\n" % l
    return s


def abs_path(relpath: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relpath))


def submit_request(addrs: typing.Set[str],
                   xml_template: str,
                   fields_map: typing.Dict[str, str]) \
        -> etree.ElementTree:
    """
    Send a wsd xml/soap request to the specified address, and wait for response.

    :param addr: the address of the wsd service
    :type addr: str
    :param xml_template: the *name* of the template file to use as payload.\
    Should be of the form "prefix__some_words_for_description.xml"
    :type xml_template: str
    :param fields_map: the dictionary containing the values needed to fill the loaded XML template
    :type fields_map: {str: str}
    :return: the full XML response message
    :rtype: lxml.etree.ElementTree
    """
    op_name = " ".join(xml_template.split("__")[1].split(".")[0].split("_")).upper()
    data = message_from_file(abs_path("templates/%s" % xml_template), **fields_map)
    if debug:
        r = etree.fromstring(data.encode("ASCII"), parser=parser)
        print('##\n## %s REQUEST\n##\n' % op_name)
        log_xml(r)
        print(etree.tostring(r, pretty_print=True, xml_declaration=True).decode("ASCII"))

    for addr in addrs:
        # TODO: handle ipv6 link-local addresses, remember to specify interface in URI
        # requests.post('http://[fe80::4aba:4eff:fec9:3d84%wlp3s0]:3911/', ...)
        r = None
        min_delay = 50
        max_delay = 250
        upper_delay = 500
        try:
            repeat = 2
            t = random.uniform(min_delay, max_delay)
            while repeat:
                try:
                    r = requests.post(addr, headers=headers, data=data, timeout=5)
                    break
                except requests.Timeout:
                    time.sleep(t)
                    t = t*2 if t*2 < upper_delay else upper_delay
                    repeat -= 1
        except requests.ConnectionError:
            continue
        if r is None:
            continue

        x = etree.fromstring(r.content)
        if debug:
            print('##\n## %s RESPONSE\n##\n' % op_name)
            log_xml(x)
            print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode("ASCII"))
        return x

    raise StopIteration


def check_fault(xml_soap_tree: etree.ElementTree) \
        -> bool:
    """
    Check if this soap message represents a Fault or not

    :param xml_soap_tree: an xml tree obtained by parsing a wsd service reply
    :type xml_soap_tree: lxml.etree.ElementTree
    :return: True if a fault message is detected, False otherwise
    :rtype: bool
    """
    action = xml_find(xml_soap_tree, ".//wsa:Action").text
    if action == 'http://schemas.xmlsoap.org/ws/2004/08/addressing/fault':
        code = xml_find(xml_soap_tree, ".//soap:Code/soap:Value").text
        subcode = xml_find(xml_soap_tree, ".//soap:Subcode/soap:Value").text
        reason = xml_find(xml_soap_tree, ".//soap:Reason/soap:Text").text
        detail = xml_find(xml_soap_tree, ".//soap:Detail").text
        if debug:
            print('##\n## FAULT\n##\n')
            print("Code: %s\n" % code)
            print("Subcode: %s\n" % subcode)
            print("Reason: %s\n" % reason)
            print("Details: %s\n" % detail)
        return True
    else:
        return False


def xml_find(xml_tree: etree.ElementTree,
             query: str) \
        -> typing.Union[etree.ElementTree, None]:
    """
    Wrapper for etree.find() method. When parsing wsd xml/soap messages, you should use this wrapper,
    because it encapsulates all the xml namespaces needed and avoids coding errors.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :param query: the XPath query
    :type query: str
    :return: the searched etree if found, or None otherwise
    :rtype: lxml.etree.ElementTree | None
    """

    return xml_tree.find(query, NSMAP)


def xml_findall(xml_tree: etree.ElementTree,
                query: str) \
        -> typing.Union[etree.ElementTree, None]:
    """
    Wrapper for etree.findall() method. When parsing wsd xml/soap messages, you should use this wrapper,
    because it encapsulates all the xml namespaces needed and avoids coding errors.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :param query: the XPath query
    :type query: str
    :return: a list of searched etrees if found, or None otherwise
    :rtype: lxml.etree.ElementTree | None
    """

    return xml_tree.findall(query, NSMAP)


def get_action_id(xml_tree: etree.ElementTree) -> str:
    return xml_find(xml_tree, ".//wsa:Action").text


def get_body_tree(xml_tree: etree.ElementTree) -> typing.Union[etree.ElementTree, None]:
    return xml_find(xml_tree, ".//soap:Body")


def get_header_tree(xml_tree: etree.ElementTree) -> typing.Union[etree.ElementTree, None]:
    return xml_find(xml_tree, ".//soap:Header")


def get_xml_str(xml_tree: etree.ElementTree, query: str) -> typing.Union[str, None]:
    q = xml_find(xml_tree, query)
    return q.text if q is not None else None


def get_xml_str_set(xml_tree: etree.ElementTree, query: str) -> typing.Union[typing.Set[str], None]:
    q = xml_find(xml_tree, query)
    return set(q.text.split()) if q is not None else None


def get_xml_int(xml_tree: etree.ElementTree, query: str) -> typing.Union[int, None]:
    q = xml_find(xml_tree, query)
    return int(q.text) if q is not None else None


def register_message_parser(action: str, msg_parser: typing.Callable) -> None:
    wsd_globals.message_parsers[action] = msg_parser


def unregister_message_parser(action: str) -> None:
    del wsd_globals.message_parsers[action]


def parse(xml_tree: etree.ElementTree):
    a = get_action_id(xml_tree)
    if a in wsd_globals.message_parsers:
        return wsd_globals.message_parsers[a](xml_tree)


def record_message_id(msg_id: str) -> bool:
    if str in wsd_globals.last_msg_ids:
        return False
    wsd_globals.last_msg_ids[wsd_globals.last_msg_idx] = msg_id
    wsd_globals.last_msg_idx += 1

def log_xml(xml_tree: etree.ElementTree):
    logfile = open(log_path + "/" + datetime.datetime.now().isoformat(), "w")
    logfile.write(etree.tostring(xml_tree, pretty_print=True, xml_declaration=True).decode("ASCII"))


def enable_debug(f: bool = True) -> None:
    global debug
    debug = f


def init():
    wsd_globals.urn = gen_urn()
    try:
        os.mkdir(log_path)
    except FileExistsError:
        pass

init()