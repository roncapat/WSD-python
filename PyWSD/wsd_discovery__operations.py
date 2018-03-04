#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import copy
import os
import pickle
import socket
import sqlite3
import struct

import lxml.etree as etree

# noinspection PyUnresolvedReferences
import wsd_common
import wsd_discovery__structures
import wsd_transfer__operations

multicast_group = ('239.255.255.250', 3702)


def send_multicast_soap_msg(xml_template, fields_map, timeout):
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


def read_soap_msg_from_socket(sock, target_service, operation_str):
    try:
        data, server = sock.recvfrom(4096)
    except socket.timeout:
        if wsd_common.debug:
            print('##\n## TIMEOUT\n##\n')
        return False
    else:
        x = etree.fromstring(data)
        if wsd_common.debug:
            print('##\n## %s MATCH\n## %s\n##\n' % (operation_str, server[0]))
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
              type_filter: str = None):
    """
    Send a multicast discovery probe message, and wait for wsd-enabled devices to respond.

    :param probe_timeout: the number of seconds to wait for probe replies
    :param type_filter: a string of space-separated device types
    :return: a list of wsd targets
    """

    opt_types = "" if type_filter is None else "<d:Types>%s</d:Types>" % type_filter

    fields = {"FROM": wsd_common.urn,
              "OPT_TYPES": opt_types}
    sock = send_multicast_soap_msg("ws-discovery__probe.xml",
                                   fields,
                                   probe_timeout)

    target_services_list = set()

    while True:
        ts = read_soap_msg_from_socket(sock, wsd_discovery__structures.TargetService(), "PROBE")
        if ts is False:
            break
        target_services_list.add(ts)

    sock.close()
    return target_services_list


def wsd_resolve(target_service: wsd_discovery__structures.TargetService):
    """
    Send a multicast resolve message, and wait for the targeted service to respond.

    :param target_service: A wsd target to resolve
    :return: an updated TargetService with additional information gathered from resolving
    """

    fields = {"FROM": wsd_common.urn,
              "EP_ADDR": target_service.ep_ref_addr}
    sock = send_multicast_soap_msg("ws-discovery__resolve.xml",
                                   fields,
                                   1)

    ts = read_soap_msg_from_socket(sock, target_service, "RESOLVE")

    sock.close()

    if ts is False:
        return target_service
    else:
        return ts


def get_devices(cache: bool = True,
                discovery: bool = True,
                probe_timeout: int = 3,
                type_filter: str = None):
    """
    Get a list of available wsd-enabled devices

    :param cache: True if you want to use the database pointed by *WSD_CACHE_PATH* env variable \
    as a way to know about already discovered devices or not.
    :param discovery: True if you want to rely on multicast probe for device discovery.
    :param probe_timeout: the amount of seconds to wait for a probe response
    :param type_filter: a string of space-separated device types
    :return: a list of wsd targets as TargetService instances
    """
    d_resolved = set()
    c = set()
    c_ok = set()

    if discovery is True:
        d = wsd_probe(probe_timeout, type_filter)

        for t in d:
            d_resolved.add(wsd_resolve(t))

    # TODO: return only entries that match the type_filter
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
        cursor.execute('SELECT DISTINCT EpRefAddr, SerializedTarget FROM WsdCache')
        for row in cursor:
            c.add(pickle.loads(row[1].encode()))

        # Discard not-reachable targets
        c_ok = copy.deepcopy(c)
        for t in c:
            if wsd_transfer__operations.wsd_get(t) is False:
                cursor.execute('DELETE FROM WsdCache WHERE EpRefAddr=?', t.ep_ref_addr)
            else:
                c_ok.add(t)
        db.commit()

        # Add discovered entries to DB
        for i in d_resolved:
            cursor.execute('INSERT OR REPLACE INTO WsdCache(EpRefAddr, SerializedTarget) VALUES (?, ?)',
                           (i.ep_ref_addr, pickle.dumps(i, 0).decode(),))
        db.commit()

        db.close()

    return set.union(c_ok, d_resolved)


def __demo():
    wsd_common.init()
    wsd_common.debug = True
    tsl = get_devices(probe_timeout=3, type_filter="wscn:ScanDeviceType")
    for a in tsl:
        print(a)


if __name__ == "__main__":
    __demo()
