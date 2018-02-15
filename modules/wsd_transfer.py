#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
from wsd_common import *
from wsd_structures import *

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

def WSD_Get(target_service):
    data = messageFromFile(AbsPath("../templates/ws-transfer_get.xml"), FROM=urn, TO=target_service.ep_ref_addr)
    r = requests.post(target_service.xaddrs[0], headers=headers, data=data)

    #print(r.status_code, r.reason)
    x = etree.fromstring(r.text)
    if debug: print ('##\n## GET RESPONSE\n## %s\n##\n' % target_service.ep_ref_addr)
    if debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))
    meta = x.find(".//mex:Metadata", NSMAP)
    metaModel = meta.find(".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisModel']", NSMAP)
    metaDev = meta.find(".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisDevice']", NSMAP)
    metaRel = meta.find(".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/Relationship']", NSMAP)

    ti = TargetInfo()
    ## WSD-PRofiles section 5.1 (+ PNP-X)
    ti.manufacturer = metaModel.find(".//wsdp:Manufacturer", NSMAP).text
    ti.manufacturer_url = metaModel.find(".//wsdp:ManufacturerUrl", NSMAP).text 
    ti.model_name = metaModel.find(".//wsdp:ModelName", NSMAP).text 
    ti.model_number = metaModel.find(".//wsdp:ModelNumber", NSMAP).text 
    ti.model_url = metaModel.find(".//wsdp:ModelUrl", NSMAP).text 
    ti.presentation_url = metaModel.find(".//wsdp:PresentationUrl", NSMAP).text 
    ti.device_cat = metaModel.find(".//pnpx:DeviceCategory", NSMAP).text.split()
    ti.friendly_name = metaDev.find(".//wsdp:FriendlyName",NSMAP).text 
    ti.fw_ver = metaDev.find(".//wsdp:FirmwareVersion",NSMAP).text 
    ti.serial_num = metaDev.find(".//wsdp:SerialNumber",NSMAP).text

    hss = []
    ## WSD-PRofiles section 5.2 (+ PNP-X)
    metaRel.findall(".//wsdp:Relationship[@Type='http://schemas.xmlsoap.org/ws/2006/02/devprof/host']", NSMAP)
    for r in metaRel:
        # UNCLEAR how the host item should differ from the target service endpoint, and how to manage multiple host items
        # TBD - need some real-case examples
        #host = r.find(".//wsdp:Host", NSMAP)
        #if host:    #"if omitted, implies the same endpoint reference of the targeted service"
        #    host.find(".//wsdp:Types", NSMAP).text 
        #    host.find(".//wsdp:ServiceId", NSMAP).text 
        #    er = host.find(".//wsa:EndpointReference", NSMAP)
        #    er.find(".//wsa:Address", NSMAP).text  #Optional endpoint fields not implemented yet
        hosted = metaRel.findall(".//wsdp:Hosted", NSMAP)
        for h in hosted:
            hs = HostedService()
            hs.types = h.find(".//wsdp:Types",NSMAP).text.split() 
            hs.service_id = h.find(".//wsdp:ServiceId",NSMAP).text
            hs.hardware_id = h.find(".//pnpx:HardwareId",NSMAP).text
            hs.compatible_id = h.find(".//pnpx:CompatibleId",NSMAP).text
            q = h.find(".//wsdp:ServiceAddress",NSMAP)
            if q: hs.service_address = q.text
            er = h.find(".//wsa:EndpointReference", NSMAP)
            hs.ep_ref_addr = er.find(".//wsa:Address", NSMAP).text
            hss.append(hs)

    ## WSD-PRofiles section 5.3 and 5.4 omitted
    return (ti, hss)

if __name__ == "__main__":
    (debug, timeout) = parseCmdLine()
    urn = genUrn()
    tsl = wsd_discovery.WSD_Probe()
    for a in tsl:
        print(a)
        (ti, hss) = WSD_Get(a)
        print(ti)
        for b in hss:
            print(b)
