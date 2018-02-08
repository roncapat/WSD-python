#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
import wsd_transfer

from wsd_common import *

import uuid
import argparse
import requests
import lxml.etree as etree

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
"wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
"sca": "http://schemas.microsoft.com/windows/2006/08/wdp/scan"}

def WSD_GetScannerElements(hosted_print_service):
    data = messageFromFile("ws-scan_getscannerelements.xml", FROM=urn, TO=hosted_print_service.ep_ref_addr)
    r = requests.post(hosted_print_service.ep_ref_addr, headers=headers, data=data)

    x = etree.fromstring(r.text)
    if debug: print ('##\n## GET SCANNER ELEMENTS RESPONSE\n##\n')
    if debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))
    re = x.find(".//sca:ScannerElements", NSMAP)
    scaStatus = re.find(".//sca:ScannerStatus", NSMAP)
    scaConfig = re.find(".//sca:ScannerConfiguration", NSMAP)
    scaDescr = re.find(".//sca:ScannerDescription", NSMAP)
    print (etree.tostring(scaStatus, pretty_print=True).decode('ascii'))
    print (etree.tostring(scaConfig, pretty_print=True).decode('ascii'))
    print (etree.tostring(scaDescr, pretty_print=True).decode('ascii'))

    scaDescr.find(".//sca:ScannerName", NSMAP)
    q = scaDescr.find(".//sca:ScannerInfo", NSMAP)
    q = scaDescr.find(".//sca:ScannerLocation", NSMAP)

    scaStatus.find(".//sca:ScannerCurrentTime", NSMAP)
    scaStatus.find(".//sca:ScannerState", NSMAP)
    ac = scaStatus.find(".//sca:ActiveConditions", NSMAP)
    dcl = ac.findall(".//sca:DeviceCondition", NSMAP)
    for dc in dcl:
        dc.find(".//sca:Time",NSMAP)
        dc.find(".//sca:Name",NSMAP)
        dc.find(".//sca:Component",NSMAP)
        dc.find(".//sca:Severity",NSMAP)
    q = scaStatus.find(".//sca:ScannerStateReasons", NSMAP)
    if q is not None: q.findall(".//sca:ScannerStateReason", NSMAP)
    q = scaStatus.find(".//sca:ConditionHistory", NSMAP)
    if q is not None:
        chl = q.findall(".//sca:ConditionHistoryEntry", NSMAP)
        for che in chl:
            che.find(".//sca:Time",NSMAP)
            che.find(".//sca:Name",NSMAP)
            che.find(".//sca:Component",NSMAP)
            che.find(".//sca:Severity",NSMAP)
            che.find(".//sca:ClearTime", NSMAP)
            
    #TODO: scaConfig parsing

if __name__ == "__main__":
    (debug, timeout) = parseCmdLine()
    urn = genUrn()
    tsl = wsd_discovery.WSD_Probe()
    for a in tsl:
        print(a)
        (ti, hss) = wsd_transfer.WSD_Get(a)
        for b in hss:
            if "wscn:ScannerServiceType" in b.types:
                print(b)
                #debug = True
                WSD_GetScannerElements(b)
