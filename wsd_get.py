#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
from wsd_discovery import _debug

import uuid
import argparse
import requests
import lxml.etree as etree

_urn = ""

def genUrn():
    return "urn:uuid:" + str(uuid.uuid4())

def messageFromFile(fname, **kwargs):
    req = ''.join(open(fname).readlines())
    for k in kwargs:
        req = req.replace('{{'+k+'}}', str(kwargs[k]))
    return req

headers={'user-agent': 'WSDAPI', 'content-type': 'application/soap+xml'}

def WSD_Get(target_service):
    data = messageFromFile("ws-transfer_get.xml", FROM=_urn, TO=target_service.ep_ref_addr)
    r = requests.post(target_service.xaddrs[0], headers=headers, data=data)

    #print(r.status_code, r.reason)
    if _debug: print ('##\n## GET RESPONSE\n## %s\n##\n' % target_service.ep_ref_addr)
    if _debug: print(r.text)

if __name__ == "__main__":
    wsd_discovery.parseCmdLine()
    _debug = True
    genUrn()
    tsl = wsd_discovery.WSD_Probe()
    for a in tsl:
        print(a)
        WSD_Get(a)
