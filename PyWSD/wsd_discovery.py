#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import pickle
import socket
import sqlite3
import struct

from wsd_structures import *

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
         "wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
         "wsd": "http://schemas.xmlsoap.org/ws/2005/04/discovery",
         "wsdp": "http://schemas.xmlsoap.org/ws/2006/02/devprof",
         "wprt": "http://schemas.microsoft.com/windows/2006/08/wdp/print",
         "wscn": "http://schemas.microsoft.com/windows/2006/08/wdp/scan",
         "i": "http://printer.example.org/2003/imaging"}


def wsd_probe():
    """
    Send a multicast discovery probe message, and wait for wsd-enabled devices to respond.

    :return: a list of wsd targets
    """
    message = message_from_file(abs_path("../templates/ws-discovery_probe.xml"), FROM=urn)
    multicast_group = ('239.255.255.250', 3702)

    target_services_list = set()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    # Remember to allow incoming UDP packets in system firewall

    try:
        if debug:
            r = etree.fromstring(message, parser=parser)
            print('##\n## PROBE\n##\n')
            print(etree.tostring(r, pretty_print=True, xml_declaration=True))
        sock.sendto(message.encode("UTF-8"), multicast_group)

        while True:
            try:
                data, server = sock.recvfrom(4096)
            except socket.timeout:
                if debug:
                    print('##\n## TIMEOUT\n##\n')
                break
            else:
                x = etree.fromstring(data)
                if debug:
                    print('##\n## PROBE MATCH\n## %s\n##\n' % server[0])
                    print(etree.tostring(x, pretty_print=True, xml_declaration=True))
                ts = TargetService()
                ts.ep_ref_addr = x.find(".//wsa:Address", NSMAP).text  # Optional endpoint fields not implemented yet
                q = x.find(".//wsd:Types", NSMAP)
                if q is not None:
                    ts.types = q.text.split()
                q = x.find(".//wsd:Scopes", NSMAP)
                if q is not None:
                    ts.scopes = q.text.split()
                q = x.find(".//wsd:XAddrs", NSMAP)
                if q is not None:
                    ts.xaddrs = q.text.split()
                ts.meta_er = int(x.find(".//wsd:MetadataVersion", NSMAP).text)
                target_services_list.add(ts)

    finally:
        sock.close()
        return target_services_list


def get_devices(cache=True, discovery=True):
    """
    Get a list of available wsd-enabled devices

    :param cache: True if you want to use the database pointed by *WSD_CACHE_PATH* env variable \
    as a way to know about already discovered devices or not.
    :param discovery: True if you want to rely on multicast probe for device discovery.

    :return: a list of wsd targets
    """
    d = set()
    c = set()

    if discovery is True:
        d = wsd_probe()

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

        # Add discovered entries to DB
        for i in d:
            cursor.execute('INSERT INTO WsdCache(SerializedTarget) VALUES (?)', (pickle.dumps(i, 0).decode(),))
        db.commit()

        db.close()

        # TODO: validates db entries, some devices may have disappeared from the local network

    return set.union(c, d)


if __name__ == "__main__":
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    debug = True
    tsl = get_devices()
    for a in tsl:
        print(a)
