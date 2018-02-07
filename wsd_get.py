#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
from wsd_discovery import _debug

import uuid
import argparse
import requests
import lxml.etree as etree

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
"wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
"mex": "http://schemas.xmlsoap.org/ws/2004/09/mex",
"wsdp": "http://schemas.xmlsoap.org/ws/2006/02/devprof",
"wprt": "http://schemas.microsoft.com/windows/2006/08/wdp/print",
"wscn": "http://schemas.microsoft.com/windows/2006/08/wdp/scan",
"pnpx": "http://schemas.microsoft.com/windows/pnpx/2005/10",
"df": "http://schemas.microsoft.com/windows/2008/09/devicefoundation"}

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
    x = etree.fromstring(r.text)
    if _debug: print ('##\n## GET RESPONSE\n## %s\n##\n' % target_service.ep_ref_addr)
    #if _debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))
    meta = x.find(".//mex:Metadata", NSMAP)
    metaModel = meta.find(".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisModel']", NSMAP)
    metaDev = meta.find(".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisDevice']", NSMAP)
    metaRel = meta.find(".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/Relationship']", NSMAP)

    ## WSD-PRofiles section 5.1
    metaModel.find(".//wsdp:Manufacturer", NSMAP)
    metaModel.find(".//wsdp:ManufacturerUrl", NSMAP)  
    metaModel.find(".//wsdp:ModelName", NSMAP)
    metaModel.find(".//wsdp:ModelNumber", NSMAP)
    metaModel.find(".//wsdp:ModelUrl", NSMAP)
    metaModel.find(".//wsdp:PresentationUrl", NSMAP)
    metaModel.find(".//pnpx:DeviceCategory", NSMAP)
    metaDev.find(".//wsdp:FriendlyName",NSMAP)
    metaDev.find(".//wsdp:FirmwareVersion",NSMAP)
    metaDev.find(".//wsdp:SerialNumber",NSMAP)
    metaDev.find(".//wsdp:FriendlyName",NSMAP)

    ## WSD-PRofiles section 5.2
    metaRel.findall(".//wsdp:Relationship[@Type='http://schemas.xmlsoap.org/ws/2006/02/devprof/host']")
    for r in metaRel:
        host = r.find(".//wsdp:Host", NSMAP)
        if host:
            host.find(".//wsdp:Types", NSMAP)
            host.find(".//wsdp:ServiceId", NSMAP)
            host.find(".//wsdp:Types", NSMAP)
            er = host.find(".//wsa:EndpointReference", NSMAP)
            er.find(".//wsa:Address", NSMAP) #Optional endpoint fields not implemented yet
        hosted = metaRel.findall(".//wsdp:Hosted", NSMAP)
        for h in hosted:
            h.find(".//wsdp:Types",NSMAP)
            h.find(".//wsdp:ServiceId",NSMAP)
            h.find(".//pnpx:hardwareId",NSMAP)
            h.find(".//pnpx:compatibleId",NSMAP)
            h.find(".//wsdp:ServiceAddress",NSMAP)
            er = h.find(".//wsa:EndpointReference", NSMAP)
            er.find(".//wsa:Address", NSMAP)

    ## WSD-PRofiles section 5.3 and 5.4 omitted

if __name__ == "__main__":
    wsd_discovery.parseCmdLine()
    _debug = True
    genUrn()
    tsl = wsd_discovery.WSD_Probe()
    for a in tsl:
        print(a)
        WSD_Get(a)
