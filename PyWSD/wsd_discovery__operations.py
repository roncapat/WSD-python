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
from wsd_discovery__structures import *
from wsd_transfer__operations import *


def wsd_probe(probe_timeout=3):
    """
    Send a multicast discovery probe message, and wait for wsd-enabled devices to respond.

    :param probe_timeout: the number of seconds to wait for probe replies
    :return: a list of wsd targets
    """
    # TODO: allow device types filtering
    message = wsd_common.message_from_file(wsd_common.abs_path("../templates/ws-discovery__probe.xml"),
                                           FROM=wsd_common.urn)
    multicast_group = ('239.255.255.250', 3702)

    target_services_list = set()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(probe_timeout)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    # Remember to allow incoming UDP packets in system firewall

    if wsd_common.debug:
        r = etree.fromstring(message.encode("ASCII"), parser=wsd_common.parser)
        print('##\n## PROBE\n##\n')
        print(etree.tostring(r, pretty_print=True, xml_declaration=True).decode("ASCII"))
    sock.sendto(message.encode("UTF-8"), multicast_group)

    while True:
        try:
            data, server = sock.recvfrom(4096)
        except socket.timeout:
            if wsd_common.debug:
                print('##\n## TIMEOUT\n##\n')
            break
        else:
            x = etree.fromstring(data)
            if wsd_common.debug:
                print('##\n## PROBE MATCH\n## %s\n##\n' % server[0])
                print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode("ASCII"))
            ts = TargetService()
            ts.ep_ref_addr = wsd_common.xml_find(x, ".//wsa:Address").text
            # FIXME: optional endpoint fields not implemented yet
            q = wsd_common.xml_find(x, ".//wsd:Types")
            if q is not None:
                ts.types = q.text.split()
            q = wsd_common.xml_find(x, ".//wsd:Scopes")
            if q is not None:
                ts.scopes = q.text.split()
            q = wsd_common.xml_find(x, ".//wsd:XAddrs")
            if q is not None:
                ts.xaddrs = q.text.split()
            ts.meta_er = int(wsd_common.xml_find(x, ".//wsd:MetadataVersion").text)
            target_services_list.add(ts)
            # TODO: rely on wsd_resolve for xaddrs field presence

    sock.close()
    return target_services_list


def get_devices(cache=True, discovery=True, probe_timeout=3):
    """
    Get a list of available wsd-enabled devices

    :param cache: True if you want to use the database pointed by *WSD_CACHE_PATH* env variable \
    as a way to know about already discovered devices or not.
    :param discovery: True if you want to rely on multicast probe for device discovery.
    :param probe_timeout: the amount of seconds to wait for a probe response

    :return: a list of wsd targets as TargetService instances
    """
    d = set()
    c = set()
    c_ok = set()

    if discovery is True:
        d = wsd_probe(probe_timeout)

    # TODO: avoid duplicate entries in db
    if cache is True:
        # Open the DB, if exists, or create a new one
        p = os.environ.get("WSD_CACHE_PATH", "")
        if p == "":
            p = os.path.expanduser("~/.wsdcache.db")
            os.environ["WSD_CACHE_PATH"] = p

        db = sqlite3.connect(p)
        cursor = db.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS WsdCache (SerializedTarget TEXT);")
        db.commit()

        # Read entries from DB
        cursor.execute('SELECT DISTINCT SerializedTarget FROM WsdCache')
        for row in cursor:
            c.add(pickle.loads(row[0].encode()))

        # Discard not-reachable targets
        c_ok = copy.deepcopy(c)
        for t in c:
            if wsd_get(t) is False:
                cursor.execute('DELETE FROM WsdCache WHERE SerializedTarget=?', (pickle.dumps(t, 0).decode(),))
            else:
                c_ok.add(t)
        db.commit()

        # Add discovered entries to DB
        for i in d:
            cursor.execute('INSERT INTO WsdCache(SerializedTarget) VALUES (?)', (pickle.dumps(i, 0).decode(),))
        db.commit()

        db.close()

    return set.union(c_ok, d)


def __demo():
    wsd_common.init()
    wsd_common.debug = True
    tsl = get_devices(probe_timeout=3)
    for a in tsl:
        print(a)


if __name__ == "__main__":
    __demo()
