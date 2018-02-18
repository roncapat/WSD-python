#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import argparse
import os
import requests
import uuid

import lxml.etree as etree

headers = {'user-agent': 'WSDAPI', 'content-type': 'application/soap+xml'}
debug = False
timeout = 2
urn = ""


def gen_urn():
    return "urn:uuid:" + str(uuid.uuid4())


def message_from_file(fname, **kwargs):
    req = ''.join(open(fname).readlines())
    for k in kwargs:
        req = req.replace('{{' + k + '}}', str(kwargs[k]))
    return req


def parse_cmd_line():
    parser = argparse.ArgumentParser(description='WSD Discovery Scanner')
    parser.add_argument('-D', action="store_true", default=False, required=False, help='Enable debug')
    parser.add_argument('-T', action="store", required=False, type=int, default=2, help='Timeout')

    args = parser.parse_args()
    return args.D, args.T


def indent(text):
    s = ""
    for l in text.splitlines():
        s += "\t%s\n" % l
    return s


def abs_path(relpath):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relpath))


def submit_request(addr, xml_template, fields_map, op_name):
    data = message_from_file(abs_path("../templates/%s" % xml_template), **fields_map)

    if debug:
        print('##\n## %s REQUEST\n##\n%s\n' % (op_name, data))
    r = requests.post(addr, headers=headers, data=data)

    x = etree.fromstring(r.text)
    if debug:
        print('##\n## %s RESPONSE\n##\n', op_name)
    if debug:
        print(etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))
    return x
