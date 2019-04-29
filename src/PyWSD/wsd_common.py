#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import datetime
import os
import random
import time
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


def gen_urn() \
        -> str:
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


def indent(text: str) \
        -> str:
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


def abs_path(relpath: str) \
        -> str:
    """
    Obtain the absolute path of a file or folder, given its relative path from PyWSD directory.
    :param relpath: the relative path
    :return: the absolute path
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relpath))


def soap_post_unicast(addr: str,
                      data: str) \
        -> typing.Union[str, None]:
    """
    Send a SOAP message as an HTTP POST request.
    Implements the retry mechanism specified in the SOAP-over-UDP specification.
    :param addr: the address to send the message to
    :type addr: str
    :param data: the message content
    :type data: str
    :return: the reply message, if any
    :rtype: str | None
    """
    min_delay = 50
    max_delay = 250
    upper_delay = 500
    try:
        repeat = 2
        t = random.uniform(min_delay, max_delay)
        while repeat:
            try:
                return requests.post(addr, headers=headers, data=data, timeout=2).content
            except requests.Timeout:
                time.sleep(t / 1000.0)
                t = t * 2 if t * 2 < upper_delay else upper_delay
                repeat -= 1
        return None
    except requests.ConnectionError:
        return None


def submit_request(addrs: typing.Set[str],
                   xml_template: str,
                   fields_map: typing.Dict[str, str]) \
        -> etree.ElementTree:
    """
    Send a wsd xml/soap request to the specified device, and wait for response.
    Multiple addresses could be provided: the message will be sent to each one until
    the device replies.

    :param addrs: the addresses of the wsd service
    :type addrs: {str}
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

    if wsd_globals.debug:
        r = etree.fromstring(data.encode("ASCII"), parser=parser)
        print('##\n## %s REQUEST\n##\n' % op_name)
        log_xml(r)
        print(etree.tostring(r, pretty_print=True, xml_declaration=True).decode("ASCII"))

    for addr in addrs:
        # TODO: handle ipv6 link-local addresses, remember to specify interface in URI
        # requests.post('http://[fe80::4aba:4eff:fec9:3d84%wlp3s0]:3911/', ...)
        r = soap_post_unicast(addr, data)
        if r is None:
            continue

        x = etree.fromstring(r)

        if wsd_globals.debug:
            print('##\n## %s RESPONSE\n##\n' % op_name)
            log_xml(x)
            print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode("ASCII"))

        return x

    raise StopIteration


def check_fault(x: etree.ElementTree) \
        -> bool:
    """
    Check if this soap message represents a Fault or not

    :param x: an xml tree obtained by parsing a wsd service reply
    :type x: lxml.etree.ElementTree
    :return: True if a fault message is detected, False otherwise
    :rtype: bool
    """
    if get_action_id(x) == 'http://schemas.xmlsoap.org/ws/2004/08/addressing/fault':
        code = get_xml_str(x, ".//soap:Code/soap:Value")
        subcode = get_xml_str(x, ".//soap:Subcode/soap:Value")
        reason = get_xml_str(x, ".//soap:Reason/soap:Text")
        detail = get_xml_str(x, ".//soap:Detail")
        if wsd_globals.debug:
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


def get_xml_str(xml_tree: etree.ElementTree,
                query: str) \
        -> typing.Union[str, None]:
    """
    Search for the specified node and extract the contained text.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :param query: the XPath query
    :type query: str
    :return: the text contained in the node, if any
    :rtype: str | None
    """
    q = xml_find(xml_tree, query)
    return q.text if q is not None else None


def get_xml_str_set(xml_tree: etree.ElementTree,
                    query: str) \
        -> typing.Union[typing.Set[str], None]:
    """
    Search for the specified node and extract the contained strings.
    The text in the node is splitted considering standard separators.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :param query: the XPath query
    :type query: str
    :return: the strings contained in the node, if any
    :rtype: {str} | None
    """
    q = xml_find(xml_tree, query)
    return set(q.text.split()) if q is not None else None


def get_xml_int(xml_tree: etree.ElementTree,
                query: str) \
        -> typing.Union[int, None]:
    q = xml_find(xml_tree, query)
    """
    Search for the specified node and extract the contained integer value.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :param query: the XPath query
    :type query: str
    :return: the integer number contained in the node, if any
    :rtype: int | None
    """
    return int(q.text) if q is not None else None


def get_header_tree(xml_tree: etree.ElementTree) \
        -> typing.Union[etree.ElementTree, None]:
    """
    Extracts the xml node containing the SOAP header of the message, if any.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :return: the SOAP header node
    :rtype: etree.ElementTree | None
    """
    return xml_find(xml_tree, ".//soap:Header")


def get_body_tree(xml_tree: etree.ElementTree) \
        -> typing.Union[etree.ElementTree, None]:
    """
    Extracts the xml node containing the SOAP body of the message, if any.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :return: the SOAP body node
    :rtype: etree.ElementTree | None
    """
    return xml_find(xml_tree, ".//soap:Body")


def get_action_id(xml_tree: etree.ElementTree) \
        -> typing.Union[str, None]:
    """
    Extracts the action id from the WSA-compliant SOAP message.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :return: the WSA ation URI specified in the message, if any
    :rtype: str | None
    """
    return get_xml_str(xml_tree, ".//wsa:Action")


def get_message_id(xml_tree: etree.ElementTree) \
        -> typing.Union[str, None]:
    """
    Extracts the message id from the WSA-compliant SOAP message.

    :param xml_tree: the etree element to search in
    :type xml_tree: lxml.etree.ElementTree
    :return: the WSA unique message identifier specified in the message, if any
    :rtype: str | None
    """
    return get_xml_str(xml_tree, ".//wsa:MessageID")


def register_message_parser(action: str,
                            msg_parser: typing.Callable) \
        -> None:
    """
    Associates a parser to a specific type of WSA message, globally.
    This will be the parser used by wsd_common.parse()

    :param action: the WSA action URI that the parser can handle.
    :type action: str
    :param msg_parser: a message parser. It will be called by passing the message
                       xml tree and is expected to return an object of the relevant
                       class abstracting the message
    :type msg_parser: callable
    """
    wsd_globals.message_parsers[action] = msg_parser


def unregister_message_parser(action: str) \
        -> None:
    """
    Removes the parser for a specific type of WSA message.

    :param action: the WSA action URI that the parser handle.
    :type action: str
    """
    del wsd_globals.message_parsers[action]


def parse(ws_msg: etree.ElementTree):
    """
    Executes the parser associated with the WS message class/action.
    Parsers can be registered with wsd_common.register_message_parser()

    :param ws_msg: the etree element to search in
    :type ws_msg: lxml.etree.ElementTree
    :return: an object of the relevant class abstracting the message
    """
    a = get_action_id(ws_msg)
    if a in wsd_globals.message_parsers:
        return wsd_globals.message_parsers[a](ws_msg)
    raise NotImplemented


def record_message_id(msg_id: str) \
        -> bool:
    """
    Checks if the specified message is a duplicate, and records the id if not.

    :param msg_id: the WSA message id to check
    :type msg_id: str
    :return: True if the message is not a duplicate, False otherwise.
    :rtype: bool
    """
    if msg_id in wsd_globals.last_msg_ids:
        return False
    wsd_globals.last_msg_ids[wsd_globals.last_msg_idx] = msg_id
    wsd_globals.last_msg_idx += 1
    wsd_globals.last_msg_idx %= len(wsd_globals.last_msg_ids)
    return True


def log_xml(xml_tree: etree.ElementTree) \
        -> None:
    """
    Dumps the specified xml tree in a timestamped file in the log folder.

    :param xml_tree: the node to dump
    :type xml_tree: etree.ElementTree
    """
    logfile = open(log_path + "/" + datetime.datetime.now().isoformat(), "w")
    logfile.write(etree.tostring(xml_tree, pretty_print=True, xml_declaration=True).decode("ASCII"))


def enable_debug(status: bool = True) \
        -> None:
    """
    Enables echoing of exchanged messages on standard output.
    :param status: True to enable, False to disable
    """
    wsd_globals.debug = status


#######################
# INITIALIZATION CODE #
#######################

wsd_globals.urn = gen_urn()
try:
    os.mkdir(log_path)
except FileExistsError:
    pass
