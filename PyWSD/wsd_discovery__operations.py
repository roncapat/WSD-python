#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import pickle
import select
import socket
import sqlite3
import struct
import typing

import lxml.etree as etree

from PyWSD import wsd_common, \
    wsd_discovery__structures, \
    wsd_transfer__operations

discovery_verbosity = 0

multicast_group = ('239.255.255.250', 3702)

wsd_mcast_v4 = '239.255.255.250'
wsd_mcast_v6 = 'FF02::C'
wsd_udp_port = 3702

db_path = os.environ.get("WSD_CACHE_PATH", "")
if not db_path:
    db_path = os.path.expanduser("~/.wsdcache.db")
    os.environ["WSD_CACHE_PATH"] = db_path


def get_sequence(xml_tree: etree.ElementTree) -> typing.List[int]:
    q = wsd_common.xml_find(xml_tree, ".//wsd:AppSequence")
    seq = [0, 0, 0]
    seq[0] = int(q.attrib['InstanceId'])
    if 'SequenceId' in q.attrib:
        seq[1] = int(q.attrib['SequenceId'])
    seq[2] = int(q.attrib['MessageNumber'])
    return seq


def parser_hello(xml_tree: etree.ElementTree) -> wsd_discovery__structures.HelloMessage:
    o = wsd_discovery__structures.HelloMessage()
    header = wsd_common.get_header_tree(xml_tree)
    o.message_id = wsd_common.get_xml_str(header, ".//wsa:MessageID")
    o.relates_to = wsd_common.get_xml_str(header, ".//wsa:RelatesTo")
    o.app_sequence = get_sequence(header)
    body = wsd_common.get_body_tree(xml_tree)
    o.ep_ref_addr = wsd_common.get_xml_str(body, ".//wsa:EndpointReference/wsa:Address")
    o.types = wsd_common.get_xml_str_set(body, ".//wsd:Types")
    o.scopes = wsd_common.get_xml_str_set(body, ".//wsd:Scopes")
    o.xaddrs = wsd_common.get_xml_str_set(body, ".//wsd:XAddrs")
    o.metadata_version = wsd_common.get_xml_int(body, ".//wsd:MetadataVersion")
    return o


def parser_bye(xml_tree: etree.ElementTree) -> wsd_discovery__structures.ByeMessage:
    o = wsd_discovery__structures.ByeMessage()
    header = wsd_common.get_header_tree(xml_tree)
    o.message_id = wsd_common.get_xml_str(header, ".//wsa:MessageID")
    o.app_sequence = get_sequence(header)
    body = wsd_common.get_body_tree(xml_tree)
    o.ep_ref_addr = wsd_common.get_xml_str(body, ".//wsa:EndpointReference/wsa:Address")
    return o


wsd_common.register_message_parser("http://schemas.xmlsoap.org/ws/2005/04/discovery/Hello", parser_hello)
wsd_common.register_message_parser("http://schemas.xmlsoap.org/ws/2005/04/discovery/Bye", parser_bye)


def send_multicast_soap_msg(xml_template: str,
                            fields_map: typing.Dict[str, str],
                            timeout: int) \
        -> socket.socket:
    """
    Send a wsd xml/soap multicast request, and return the opened socket.

    :param xml_template: the name of the xml template to fill and send
    :type xml_template: str
    :param fields_map: the map of placeholders and strings to substitute inside the template
    :type fields_map: {str: str}
    :param timeout: the timeout of the socket
    :type timeout: int
    :return: the socket use for message delivery
    :rtype: socket.socket
    """
    message = wsd_common.message_from_file(wsd_common.abs_path("../templates/%s" % xml_template),
                                           **fields_map)

    op_name = " ".join(xml_template.split("__")[1].split(".")[0].split("_")).upper()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    if wsd_common.debug:
        r = etree.fromstring(message.encode("ASCII"), parser=wsd_common.parser)
        print('##\n## %s\n##\n' % op_name)
        wsd_common.log_xml(r)
        print(etree.tostring(r, pretty_print=True, xml_declaration=True).decode("ASCII"))
    sock.sendto(message.encode("UTF-8"), (wsd_mcast_v4, wsd_udp_port))
    return sock


# TODO: split listening and parsing
def read_discovery_multicast_reply(sock: socket.socket,
                                   target_service: wsd_discovery__structures.TargetService,
                                   operation: str) \
        -> typing.Union[None, wsd_discovery__structures.TargetService]:
    """
    Waits for a reply from an endpoint, containing info about the target itself. Used to
    catch wsd_probe and wsd_resolve responses. Updates the target_service with data collected.

    :param sock: The socket to read from
    :type sock: socket.socket
    :param target_service: an instance of TargetService to fill or update with data received
    :param operation: label for debug purposes only
    :type operation: str
    :return: an updated target_service object, or False if the socket timeout is reached
    :rtype: wsd_discovery__structures.TargetService | False
    """
    try:
        data, server = sock.recvfrom(4096)
    except socket.timeout:
        if wsd_common.debug:
            print('##\n## TIMEOUT\n##\n')
        return None
    else:
        x = etree.fromstring(data)
        if wsd_common.debug:
            print('##\n## %s MATCH\n## %s\n##\n' % (operation, server[0]))
            wsd_common.log_xml(x)
            print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode("ASCII"))

        target_service.ep_ref_addr = wsd_common.xml_find(x, ".//wsa:Address").text
        q = wsd_common.xml_find(x, ".//wsd:Types")
        if q is not None:
            target_service.types = target_service.types.union(q.text.split())
        q = wsd_common.xml_find(x, ".//wsd:Scopes")
        if q is not None:
            target_service.scopes = target_service.scopes.union(q.text.split())
        q = wsd_common.xml_find(x, ".//wsd:XAddrs")
        if q is not None:
            target_service.xaddrs = target_service.xaddrs.union(q.text.split())
        target_service.meta_ver = int(wsd_common.xml_find(x, ".//wsd:MetadataVersion").text)
    return target_service


def open_multicast_udp_socket(addr: str, port: int) -> socket.socket:
    addrinfo = None
    for a in socket.getaddrinfo(addr, port):
        if a[1].name == 'SOCK_DGRAM':
            addrinfo = a

    if not addrinfo:
        raise ConnectionError

    sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    gbin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
    if addrinfo[0] == socket.AF_INET:
        mreq = gbin + struct.pack('=I', socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    else:
        mreq = gbin + struct.pack('@I', 0)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    return sock


def init_multicast_listener():
    sock_1 = open_multicast_udp_socket(wsd_mcast_v4, wsd_udp_port)
    return [sock_1]
    #sock_2 = open_multicast_udp_socket(wsd_mcast_v6, wsd_udp_port)
    #return [sock_1, sock_2] #TODO: enable ipv6 support once stable



def deinit_multicast_listener(sockets):
    for sock in sockets:
        sock.close()


def listen_multicast_announcements(sockets) \
        -> typing.Tuple[bool, wsd_discovery__structures.TargetService]:
    """

    """
    empty = []
    readable = []
    action = ""
    while action not in ["http://schemas.xmlsoap.org/ws/2005/04/discovery/Hello",
                         "http://schemas.xmlsoap.org/ws/2005/04/discovery/Bye"]:
        while not readable:
            readable, writable, exceptional = select.select(sockets, empty, empty)

        data, server = readable[0].recvfrom(4096)
        x = etree.fromstring(data)
        action = wsd_common.get_action_id(x)
        readable = []

    if wsd_common.debug:
        print('##\n## %s MATCH\n## %s\n##\n' % (action.split("/")[-1].upper(), server[0]))
        wsd_common.log_xml(x)
        print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode("ASCII"))

    if action == "http://schemas.xmlsoap.org/ws/2005/04/discovery/Hello":
        return True, parser_hello(x).get_target_service()
    if action == "http://schemas.xmlsoap.org/ws/2005/04/discovery/Bye":
        return False, parser_bye(x).get_target_service()


def wsd_probe(probe_timeout: int = 3,
              type_filter: typing.Set[str] = None) \
        -> typing.Set[wsd_discovery__structures.TargetService]:
    """
    Send a multicast discovery probe message, and wait for wsd-enabled devices to respond.

    :param probe_timeout: the number of seconds to wait for probe replies
    :type probe_timeout: int
    :param type_filter: a set of legal strings, each representing a device class
    :type type_filter: {str}
    :return: a set of wsd targets
    :rtype: {wsd_discovery__structures.TargetService}
    """

    opt_types = "" if type_filter is None else "<d:Types>%s</d:Types>" % ' '.join(type_filter)

    fields = {"FROM": wsd_common.urn,
              "OPT_TYPES": opt_types}
    sock = send_multicast_soap_msg("ws-discovery__probe.xml",
                                   fields,
                                   probe_timeout)

    target_services_list = set()

    while True:
        ts = read_discovery_multicast_reply(sock, wsd_discovery__structures.TargetService(), "PROBE")
        if not ts:
            break
        target_services_list.add(ts)
        discovery_log("FOUND          " + ts.ep_ref_addr)

    sock.close()
    return target_services_list


def wsd_resolve(target_service: wsd_discovery__structures.TargetService) \
        -> typing.Tuple[bool, wsd_discovery__structures.TargetService]:
    """
    Send a multicast resolve message, and wait for the targeted service to respond.

    :param target_service: A wsd target to resolve
    :type target_service: wsd_discovery__structures.TargetService
    :return: an updated TargetService with additional information gathered from resolving
    :rtype: wsd_discovery__structures.TargetService
    """

    fields = {"FROM": wsd_common.urn,
              "EP_ADDR": target_service.ep_ref_addr}
    sock = send_multicast_soap_msg("ws-discovery__resolve.xml",
                                   fields,
                                   2)

    ts = read_discovery_multicast_reply(sock, target_service, "RESOLVE")
    sock.close()

    if not ts:
        discovery_log("UNRESOLVED     " + target_service.ep_ref_addr)
        return False, target_service
    else:
        discovery_log("RESOLVED       " + ts.ep_ref_addr)
        return True, ts


def get_devices(cache: bool = True,
                discovery: bool = True,
                probe_timeout: int = 3,
                type_filter: typing.Set[str] = None) \
        -> typing.Set[wsd_discovery__structures.TargetService]:
    """
    Get a list of available wsd-enabled devices

    :param cache: True if you want to use the database pointed by *WSD_CACHE_PATH* env variable \
    as a way to know about already discovered devices or not.
    :type cache: bool
    :param discovery: True if you want to rely on multicast probe for device discovery.
    :type discovery: bool
    :param probe_timeout: the amount of seconds to wait for a probe response
    :type probe_timeout: int
    :param type_filter: a set of device types (as strings)
    :type type_filter: {str}
    :return: a list of wsd targets as TargetService instances
    :rtype: {wsd_discovery__structures.TargetService}
    """
    d_resolved = set()
    c_ok = set()

    if discovery is True:
        d = wsd_probe(probe_timeout, type_filter)

        for t in d:
            ok, t = wsd_resolve(t)
            if ok:
                d_resolved.add(t)

    if cache is True:
        db = sqlite3.connect(db_path)

        create_table_if_not_exists(db)

        c = read_targets_from_db(db)

        # Discard not-reachable targets
        for t in c:
            s = check_target_status(t)
            if s:
                c_ok.add(t)
            else:
                remove_target_from_db(db, t)

        # Add discovered entries to DB
        for i in d_resolved:
            add_target_to_db(db, i)

        db.close()

    result = set()
    for elem in set.union(c_ok, d_resolved):
        if not type_filter or not elem.types.isdisjoint(type_filter):
            result.add(elem)
    return result


def create_table_if_not_exists(db: sqlite3.Connection) -> None:
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS WsdCache (EpRefAddr TEXT PRIMARY KEY, SerializedTarget TEXT);")
    db.commit()


def check_target_status(t: wsd_discovery__structures.TargetService) -> bool:
    try:
        wsd_transfer__operations.wsd_get(t)
        discovery_log("VERIFIED       " + t.ep_ref_addr)
        return True
    except (TimeoutError, StopIteration):
        return False


def read_targets_from_db(db: sqlite3.Connection) -> typing.Set[wsd_discovery__structures.TargetService]:
    cursor = db.cursor()
    c = set()
    cursor.execute('SELECT DISTINCT EpRefAddr, SerializedTarget FROM WsdCache')
    for row in cursor:
        c.add(pickle.loads(row[1].encode()))
    return c


def add_target_to_db(db: sqlite3.Connection,
                     t: wsd_discovery__structures.TargetService) -> None:
    cursor = db.cursor()
    cursor.execute('INSERT OR REPLACE INTO WsdCache(EpRefAddr, SerializedTarget) VALUES (?, ?)',
                   (t.ep_ref_addr, pickle.dumps(t, 0).decode(),))
    discovery_log("REGISTERED     " + t.ep_ref_addr)
    db.commit()


def remove_target_from_db(db: sqlite3.Connection,
                          t: wsd_discovery__structures.TargetService) -> None:
    cursor = db.cursor()
    cursor.execute('DELETE FROM WsdCache WHERE EpRefAddr=?', (t.ep_ref_addr,))
    discovery_log("UNREGISTERED   " + t.ep_ref_addr)
    db.commit()


def set_discovery_verbosity(lvl: int):
    global discovery_verbosity
    discovery_verbosity = lvl


def discovery_log(text: str, lvl: int = 1):
    print(text) if discovery_verbosity >= lvl else None


def open_db() -> sqlite3.Connection:
    return sqlite3.connect(db_path)
