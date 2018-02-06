#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd-discovery

import argparse
import struct
import socket
import lxml.etree as etree


if __name__ == "__main__":
    tsl = WSD_Probe()
    for a in tsl: print(a)
