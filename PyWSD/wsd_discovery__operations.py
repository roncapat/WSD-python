#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import pickle
import socket
import sqlite3
import struct
import typing

import lxml.etree as etree

from PyWSD import wsd_common, \
    wsd_discovery__structures, \
    wsd_transfer__operations

multicast_group = ('239.255.255.250', 3702)


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
        print(etree.tostring(r, pretty_print=True, xml_declaration=True).decode("ASCII"))
    sock.sendto(message.encode("UTF-8"), multicast_group)
    return sock


# TODO: split listening and parsing
def read_discovery_multicast_reply(sock: socket.socket,
                                   target_service: wsd_discovery__structures.TargetService,
                                   operation: str) \
        -> typing.Union[False, wsd_discovery__structures.TargetService]:
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
        return False
    else:
        x = etree.fromstring(data)
        if wsd_common.debug:
            print('##\n## %s MATCH\n## %s\n##\n' % (operation, server[0]))
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
        if ts is False:
            break
        target_services_list.add(ts)

    sock.close()
    return target_services_list


def wsd_resolve(target_service: wsd_discovery__structures.TargetService) \
        -> wsd_discovery__structures.TargetService:
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
                                   1)

    ts = read_discovery_multicast_reply(sock, target_service, "RESOLVE")

    sock.close()

    if ts is False:
        return target_service
    else:
        return ts


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
            d_resolved.add(wsd_resolve(t))

    if cache is True:
        # Open the DB, if exists, or create a new one
        p = os.environ.get("WSD_CACHE_PATH", "")
        if p == "":
            p = os.path.expanduser("~/.wsdcache.db")
            os.environ["WSD_CACHE_PATH"] = p

        db = sqlite3.connect(p)
        cursor = db.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS WsdCache (EpRefAddr TEXT PRIMARY KEY, SerializedTarget TEXT);")
        db.commit()

        # Read entries from DB
        c = set()
        cursor.execute('SELECT DISTINCT EpRefAddr, SerializedTarget FROM WsdCache')
        for row in cursor:
            c.add(pickle.loads(row[1].encode()))

        # Discard not-reachable targets
        for t in c:
            try:
                wsd_transfer__operations.wsd_get(t)
                c_ok.add(t)
            except TimeoutError:
                cursor.execute('DELETE FROM WsdCache WHERE EpRefAddr=?', t.ep_ref_addr)
        db.commit()

        # Add discovered entries to DB
        for i in d_resolved:
            cursor.execute('INSERT OR REPLACE INTO WsdCache(EpRefAddr, SerializedTarget) VALUES (?, ?)',
                           (i.ep_ref_addr, pickle.dumps(i, 0).decode(),))
        db.commit()

        db.close()

    result = set()
    for elem in set.union(c_ok, d_resolved):
        if not elem.types.isdisjoint(type_filter):
            result.add(elem)
    return result


def __demo():
    wsd_common.init()
    wsd_common.debug = True
    tsl = get_devices(probe_timeout=3, type_filter={"wscn:ScanDeviceType"})
    for a in tsl:
        print(a)


if __name__ == "__main__":
    __demo()
