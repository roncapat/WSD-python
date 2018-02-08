#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import argparse, uuid

headers={'user-agent': 'WSDAPI', 'content-type': 'application/soap+xml'}
debug = False
timeout = 2
urn = ""

def genUrn():
    return "urn:uuid:" + str(uuid.uuid4())

def messageFromFile(fname, **kwargs):
    req = ''.join(open(fname).readlines())
    for k in kwargs:
        req = req.replace('{{'+k+'}}', str(kwargs[k]))
    return req

def parseCmdLine():
    parser = argparse.ArgumentParser(description='WSD Discovery Scanner')
    parser.add_argument('-D', action="store_true", default=False, required=False, help='Enable debug')
    parser.add_argument('-T', action="store", required=False, type=int, default=2, help='Timeout')

    args = parser.parse_args()
    return (args.D, args.T)
