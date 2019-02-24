#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import argparse
import datetime
import os
import typing
import uuid

import lxml.etree as etree
import requests

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
debug = False
urn = ""
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
    return req


def parse_cmd_line():
    args_parser = argparse.ArgumentParser(description='WSD Discovery Scanner')
    args_parser.add_argument('-D', action="store_true", default=False, required=False, help='Enable debug')
    args_parser.add_argument('-T', action="store", required=False, type=int, default=2, help='Timeout')

    args = args_parser.parse_args()
    return args.D, args.T


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


def submit_request(addr: str,
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

    data = message_from_file(abs_path("../templates/%s" % xml_template), **fields_map)

    if debug:
        r = etree.fromstring(data.encode("ASCII"), parser=parser)
        print('##\n## %s REQUEST\n##\n' % op_name)
        log_xml(r)
        print(etree.tostring(r, pretty_print=True, xml_declaration=True).decode("ASCII"))

    try:
        r = requests.post(addr, headers=headers, data=data, timeout=5)
    except (requests.ReadTimeout, requests.ConnectTimeout):
        raise TimeoutError

    x = etree.fromstring(r.text)
    if debug:
        print('##\n## %s RESPONSE\n##\n' % op_name)
        log_xml(x)
        print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode("ASCII"))
    return x


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


def log_xml(xml_tree: etree.ElementTree):
    logfile = open(log_path + "/" + datetime.datetime.now().isoformat(), "w")
    logfile.write(etree.tostring(xml_tree, pretty_print=True, xml_declaration=True).decode("ASCII"))

def init() -> None:
    global urn
    urn = gen_urn()
    try:
        os.mkdir(log_path)
    except FileExistsError:
        pass
