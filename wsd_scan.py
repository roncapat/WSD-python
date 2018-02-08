#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
import wsd_transfer

from wsd_common import *

import uuid
import argparse
import requests
import lxml.etree as etree

class ScannerCondition:
    def __init__(self):
        self.time = ""
        self.name = ""
        self.component = ""
        self.severity = ""
    def __str__(self):
        s = ""
        s += "Condition name:       %s\n" % self.name
        s += "Condition time:       %s\n" % self.time
        s += "Condition component:  %s\n" % self.component
        s += "Condition severity:   %s\n" % self.severity
        return s

class ScannerStatus:
    def __init__(self):
        self.time = ""
        self.state = ""
        self.reasons = []
        self.active_conditions = []
        self.conditions_history = [] ##tuple (time, condition)

    def __str__(self):
        s = ""
        s += "Scanner time:         %s\n" % self.time
        s += "Scanner state:        %s\n" % self.state
        s += "Reasons:              %s\n" % ", ".join(self.reasons)
        s += "Active conditions:\n"
        for ac in self.active_conditions:
            s+= str(ac)
        s += "Condition history:\n"
        for c in self.conditions_history:
            s += str(c[1])
            s += "Clear time: %s\n" % c[0]
        return s

class ScannerSettings:
    def __init__(self):
        self.formats = []
        self.compression_factor = (0,0) #(min, max)
        self.content_types = []
        self.size_autodetect_sup = False
        self.auto_exposure_sup = False
        self.brightness_sup = False
        self.contrast_sup = False
        self.scaling_range_w = (0,0) #(min, max)
        self.scaling_range_h = (0,0) #(min, max)
        self.rotations = []
        
    def __str__(self):
        s = ''
        s += "Supported formats:    %s\n" % ', '.join(self.formats)
        s += "Compression range:    %d - %d\n" % self.compression_factor
        s += "Content types:        %s\n" % ', '.join(self.content_types)
        s += "Size autodetect:      %r\n" % self.size_autodetect_sup
        s += "Auto exposure:        %r\n" % self.auto_exposure_sup
        s += "Manual brightness:    %r\n" % self.brightness_sup
        s += "Manual contrast:      %r\n" % self.contrast_sup
        s += "Width scaling:        %d - %d\n" % self.scaling_range_w
        s += "Height scaling:       %d - %d\n" % self.scaling_range_h
        s += "Rotations:            %s\n" % ', '.join(self.rotations)
        return s
    
class ScannerService:
    def __init__(self):
        self.name = ""
        self.info = ""
        self.location = ""
        self.status = ScannerStatus()
        self.settings = ScannerSettings()
        
    def __str__(self):
        s = ""
        s += "Scanner name:         %s\n" % self.name
        s += "Scanner info:         %s\n" % self.info
        s += "Scanner location:     %s\n" % self.location
        s += str(self.status)
        s += str(self.settings)
        return s

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
"wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
"sca": "http://schemas.microsoft.com/windows/2006/08/wdp/scan"}

def WSD_GetScannerElements(hosted_scan_service):
    data = messageFromFile("ws-scan_getscannerelements.xml", FROM=urn, TO=hosted_scan_service.ep_ref_addr)
    r = requests.post(hosted_scan_service.ep_ref_addr, headers=headers, data=data)

    x = etree.fromstring(r.text)
    if debug: print ('##\n## GET SCANNER ELEMENTS RESPONSE\n##\n')
    if debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))
    re = x.find(".//sca:ScannerElements", NSMAP)
    scaStatus = re.find(".//sca:ScannerStatus", NSMAP)
    scaConfig = re.find(".//sca:ScannerConfiguration", NSMAP)
    scaDescr = re.find(".//sca:ScannerDescription", NSMAP)
    stdTicket = re.find(".//sca:DefaultScanTicket", NSMAP)
    
    sc = ScannerService()

    sc.name = scaDescr.find(".//sca:ScannerName", NSMAP).text
    q = scaDescr.find(".//sca:ScannerInfo", NSMAP)
    if q is not None: sc.info = q.text
    q = scaDescr.find(".//sca:ScannerLocation", NSMAP)
    if q is not None: sc.location = q.text
    
    sc.status.time = scaStatus.find(".//sca:ScannerCurrentTime", NSMAP).text
    sc.status.state = scaStatus.find(".//sca:ScannerState", NSMAP).text
    ac = scaStatus.find(".//sca:ActiveConditions", NSMAP)
    if ac is not None:
        dcl = ac.findall(".//sca:DeviceCondition", NSMAP)
        for dc in dcl:
            c = ScannerCondition()
            c.time = dc.find(".//sca:Time",NSMAP).text
            c.name = dc.find(".//sca:Name",NSMAP).text
            c.component = dc.find(".//sca:Component",NSMAP).text
            c.severity = dc.find(".//sca:Severity",NSMAP).text
            sc.status.active_conditions.append(c)
    q = scaStatus.find(".//sca:ScannerStateReasons", NSMAP)
    if q is not None:
        dsr = q.findall(".//sca:ScannerStateReason", NSMAP)
        for sr in dsr:
            sc.status.reasons.append(sr.text)
    q = scaStatus.find(".//sca:ConditionHistory", NSMAP)
    if q is not None:
        chl = q.findall(".//sca:ConditionHistoryEntry", NSMAP)
        for che in chl:
            c = ScannerCondition()
            c.time = che.find(".//sca:Time",NSMAP).text
            c.name = che.find(".//sca:Name",NSMAP).text
            c.component = che.find(".//sca:Component",NSMAP).text
            c.severity = che.find(".//sca:Severity",NSMAP).text
            sc.status.conditions_history.append( (che.find(".//sca:ClearTime", NSMAP).text, c) )        

    ds = scaConfig.find(".//sca:DeviceSettings", NSMAP)
    pla = scaConfig.find(".//sca:Platen", NSMAP)
    adf = scaConfig.find(".//sca:ADF", NSMAP)

    s = ScannerSettings()
    q = ds.findall(".//sca:FormatsSupported/sca:FormatValue", NSMAP)
    s.formats = [x.text for x in q]
    v1 = ds.find(".//sca:CompressionQualityFactorSupported/sca:MinValue", NSMAP)
    v2 = ds.find(".//sca:CompressionQualityFactorSupported/sca:MaxValue", NSMAP)
    s.compression_factor = (int(v1.text), int(v2.text))
    q = ds.findall(".//sca:ContentTypesSupported/sca:ContentTypeValue", NSMAP)
    s.content_types = [x.text for x in q]
    q = ds.find(".//sca:DocumentSizeAutoDetectSupported", NSMAP)
    s.size_autodetect_sup = True if q.text == 'true' or q.text == '1' else False
    q = ds.find(".//sca:AutoExposureSupported", NSMAP)
    s.auto_exposure_sup = True if q.text == 'true' or q.text == '1' else False
    q = ds.find(".//sca:BrightnessSupported", NSMAP)
    s.brightness_sup = True if q.text == 'true' or q.text == '1' else False
    q = ds.find(".//sca:ContrastSupported", NSMAP)
    s.contrast_sup = True if q.text == 'true' or q.text == '1' else False
    v1 = ds.find(".//sca:ScalingRangeSupported/sca:ScalingWidth/sca:MinValue", NSMAP)
    v2 = ds.find(".//sca:ScalingRangeSupported/sca:ScalingWidth/sca:MaxValue", NSMAP)
    s.scaling_range_w = (int(v1.text), int(v2.text))
    v1 = ds.find(".//sca:ScalingRangeSupported/sca:ScalingHeight/sca:MinValue", NSMAP)
    v2 = ds.find(".//sca:ScalingRangeSupported/sca:ScalingHeight/sca:MaxValue", NSMAP)
    s.scaling_range_h = (int(v1.text), int(v2.text))
    q = ds.findall(".//sca:RotationsSupported/sca:RotationValue", NSMAP)
    s.rotations = [x.text for x in q]
    sc.settings = s

    print (etree.tostring(pla, pretty_print=True).decode('ascii'))
    print (etree.tostring(adf, pretty_print=True).decode('ascii'))

    print (etree.tostring(stdTicket, pretty_print=True).decode('ascii'))
    
    return sc
    #TODO: scaConfig  platen/adf parsing

if __name__ == "__main__":
    (debug, timeout) = parseCmdLine()
    urn = genUrn()
    tsl = wsd_discovery.WSD_Probe()
    for a in tsl:
        (ti, hss) = wsd_transfer.WSD_Get(a)
        for b in hss:
            if "wscn:ScannerServiceType" in b.types:
                sc = WSD_GetScannerElements(b)
                print(a)
                print(ti)
                print(b)
                print (sc)
