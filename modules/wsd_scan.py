#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import wsd_discovery
import wsd_transfer

from wsd_common import *
from wsd_structures import *

import uuid
import email
import copy
import argparse
import requests
import lxml.etree as etree

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
"wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
"sca": "http://schemas.microsoft.com/windows/2006/08/wdp/scan"}

def parseScanTicket(stdTicket):
    t = ScanTicket()
    t.job_name = stdTicket.find(".//sca:JobDescription/sca:JobName", NSMAP).text
    t.job_user_name = stdTicket.find(".//sca:JobDescription/sca:JobOriginatingUserName", NSMAP).text
    q = stdTicket.find(".//sca:JobDescription/sca:JobInformation", NSMAP)
    if q is not None:
        t.job_info = q.text
    dp = stdTicket.find(".//sca:DocumentParameters", NSMAP)
    t.doc_params = parseDocumentParams(dp)
    return t

def parseMediaSide(ms):
    s = MediaSide()
    r = ms.find(".//sca:ScanRegion", NSMAP)
    if r is not None:
        q = r.find(".//sca:ScanRegionXOffset", NSMAP)
        if q is not None:
            s.offset = (int(q.text),s.offset[1])
        q = r.find(".//sca:ScanRegionYOffset", NSMAP)
        if q is not None:
            s.offset = (s.offset[0], int(q.text))
        v1 = r.find(".//sca:ScanRegionWidth", NSMAP)
        v2 = r.find(".//sca:ScanRegionHeight", NSMAP)
        s.size = (int(v1.text), int(v2.text))
    q = ms.find(".//sca:ColorProcessing", NSMAP)
    if q is not None:
        s.color = q.text
    q = ms.find(".//sca:Resolution/sca:Width", NSMAP)
    s.res = (int(q.text),s.res[1])
    q = ms.find(".//sca:Resolution/sca:Height", NSMAP)
    s.res = (s.res[0], int(q.text))
    return s

def parseDocumentParams(dp):
    dest = DocumentParams()
    q = dp.find(".//sca:Format", NSMAP)
    if q is not None:
        dest.format = q.text
    q = dp.find(".//sca:CompressionQualityFactor", NSMAP)
    if q is not None:
        dest.compression_factor = q.text
    q = dp.find(".//sca:ImagesToTransfer", NSMAP)
    if q is not None:
        dest.images_num = int(q.text)
    q = dp.find(".//sca:InputSource", NSMAP)
    if q is not None:
        dest.input_src = q.text
    q = dp.find(".//sca:ContentType", NSMAP)
    if q is not None:
        dest.content_type = q.text
    q = dp.find(".//sca:InputSize", NSMAP)
    if q is not None:
        b = q.find(".//sca:DocumentAutoDetect", NSMAP)
        if b is not None:
            dest.size_autodetect = True if b.text == 'true' or b.text == '1' else False
        v1 = q.find(".//sca:InputMediaSize/sca:Width", NSMAP)
        v2 = q.find(".//sca:InputMediaSize/sca:Height", NSMAP)
        dest.input_size = (int(v1.text), int(v2.text))
    q = dp.find(".//sca:Exposure", NSMAP)
    if q is not None:
        b = q.find(".//sca:AutoExposure", NSMAP)
        if b is not None:
            dest.auto_exposure = True if b.text == 'true' or b.text == '1' else False
        dest.contrast = int(q.find(".//sca:ExposureSettings/sca:Contrast", NSMAP).text)
        dest.brightness = int(q.find(".//sca:ExposureSettings/sca:Brightness", NSMAP).text)
        dest.sharpness = int(q.find(".//sca:ExposureSettings/sca:Sharpness", NSMAP).text)
    q = dp.find(".//sca:Scaling", NSMAP)
    if q is not None:
        v1 = q.find(".//sca:ScalingWidth", NSMAP)
        v2 = q.find(".//sca:ScalingHeight", NSMAP)
        dest.scaling = (int(v1.text), int(v2.text))
    q = dp.find(".//sca:Rotation", NSMAP)
    if q is not None:
        dest.rotation = int(q.text)
    q = dp.find(".//sca:MediaSides", NSMAP)
    if q is not None:
        f = q.find(".//sca:MediaFront", NSMAP)
        dest.front = parseMediaSide(f)
        
        f = q.find(".//sca:MediaBack", NSMAP)
        if f is not None:
            dest.back = parseMediaSide(f)
        else:
            dest.back = copy.deepcopy(dest.front)
    return dest

def parseScannerCondition(sc):
    c = ScannerCondition()
    c.time = sc.find(".//sca:Time",NSMAP).text
    c.name = sc.find(".//sca:Name",NSMAP).text
    c.component = sc.find(".//sca:Component",NSMAP).text
    c.severity = sc.find(".//sca:Severity",NSMAP).text
    return c

def parseScannerSourceSettings(se, name):
    sss = ScannerSourceSettings()
    v1 = se.find(".//sca:%sOpticalResolution/sca:Width" % name, NSMAP)
    v2 = se.find(".//sca:%sOpticalResolution/sca:Height" % name, NSMAP)
    sss.optical_res = (int(v1.text), int(v2.text))
    q = se.findall(".//sca:%sResolutions/sca:Widths/sca:Width" % name, NSMAP)
    sss.width_res = [x.text for x in q]
    q = se.findall(".//sca:%sResolutions/sca:Heights/sca:Height" % name, NSMAP)
    sss.height_res = [x.text for x in q]                                                                                        
    q = se.findall(".//sca:%sColor/sca:ColorEntry" % name, NSMAP)
    sss.color_modes = [x.text for x in q]  
    v1 = se.find(".//sca:%sMinimumSize/sca:Width" % name, NSMAP)
    v2 = se.find(".//sca:%sMinimumSize/sca:Height" % name, NSMAP)
    sss.min_size = (int(v1.text), int(v2.text))
    v1 = se.find(".//sca:%sMaximumSize/sca:Width" % name, NSMAP)
    v2 = se.find(".//sca:%sMaximumSize/sca:Height" % name, NSMAP)
    sss.max_size = (int(v1.text), int(v2.text))
    return sss

def WSD_GetScannerElements(hosted_scan_service):

    #TODO: handle error messages

    data = messageFromFile(AbsPath("../templates/ws-scan_getscannerelements.xml"), FROM=urn, TO=hosted_scan_service.ep_ref_addr)
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
            c = parseScannerCondition(dc)
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
            c = parseScannerCondition(che)
            sc.status.conditions_history.append( (che.find(".//sca:ClearTime", NSMAP).text, c) )        

    ds = scaConfig.find(".//sca:DeviceSettings", NSMAP)
    pla = scaConfig.find(".//sca:Platen", NSMAP)
    adf = scaConfig.find(".//sca:ADF", NSMAP)
    ## .//sca:Film omitted

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
    if pla is not None:
        sc.platen = parseScannerSourceSettings(pla, "Platen")
    if adf is not None:
        q = adf.find(".//sca:ADFSupportsDuplex", NSMAP)
        sc.adf_duplex = True if q.text == 'true' or q.text == '1' else False
        f = adf.find(".//sca:ADFFront", NSMAP)
        b = adf.find(".//sca:ADFBack", NSMAP)
        if f is not None:
            sc.front_adf = parseScannerSourceSettings(f, "ADF")
        if b is not None:
            sc.back_adf = parseScannerSourceSettings(b, "ADF")

    sc.std_ticket = parseScanTicket(stdTicket)

    return sc

def WSD_ValidateScanTicket(hosted_scan_service, ticket):

    data = messageFromFile(AbsPath("../templates/ws-scan_validatescanticket.xml"),
                           FROM=urn,
                           TO=hosted_scan_service.ep_ref_addr,
                           **ticket.asMap())
    r = requests.post(hosted_scan_service.ep_ref_addr, headers=headers, data=data)

    #TODO: handle error messages

    if debug: print ('##\n## VALIDATE SCAN TICKET REQUEST\n##\n%s' % data)

    x = etree.fromstring(r.text)
    if debug: print ('##\n## VALIDATE SCAN TICKET RESPONSE\n##\n')
    if debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))

    b = x.find(".//sca:ValidTicket", NSMAP)
    is_valid = True if b.text == 'true' or b.text == '1' else False
    if is_valid:
        return (True, ticket)
    else:
        return (False, parseScanTicket(x.find(".//sca::ValidScanTicket", NSMAP)))

def WSD_CreateScanJob(hosted_scan_service, ticket):
    
    data = messageFromFile(AbsPath("../templates/ws-scan_createscanjob.xml"),
                           FROM=urn,
                           TO=hosted_scan_service.ep_ref_addr,
                           **ticket.asMap())
    
    if debug: print ('##\n## CREATE SCAN JOB REQUEST\n##\n%s' % data)
    r = requests.post(hosted_scan_service.ep_ref_addr, headers=headers, data=data)

    x = etree.fromstring(r.text)
    if debug: print ('##\n## CREATE SCAN JOB RESPONSE\n##\n')
    if debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))

    j = ScanJob()
    x = x.find(".//sca:CreateScanJobResponse", NSMAP)
    j.id = int(x.find(".//sca:JobId", NSMAP).text)
    j.token = x.find(".//sca:JobToken", NSMAP).text
    q = x.find(".//sca:ImageInformation/sca:MediaFrontImageInfo", NSMAP)
    j.f_pixel_line = int(q.find("sca:PixelsPerLine", NSMAP).text)
    j.f_num_lines = int(q.find("sca:NumberOfLines", NSMAP).text)
    j.f_byte_line = int(q.find("sca:BytesPerLine", NSMAP).text)
    q = x.find(".//sca:ImageInformation/sca:MediaBackImageInfo", NSMAP)
    if q is not None:
        j.b_pixel_line = int(q.find("sca:PixelsPerLine", NSMAP).text)
        j.b_num_lines = int(q.find("sca:NumberOfLines", NSMAP).text)
        j.b_byte_line = int(q.find("sca:BytesPerLine", NSMAP).text)
    dp = x.find(".//sca:DocumentFinalParameters", NSMAP)
    j.doc_params = parseDocumentParams(dp)

    return j

def WSD_RetrieveImage(hosted_scan_service, job, docname):
    data = messageFromFile(AbsPath("../templates/ws-scan_retrieveimage.xml"),
                       FROM=urn,
                       TO=hosted_scan_service.ep_ref_addr,
                       JOB_ID=job.id,
                       JOB_TOKEN=job.token,
                       DOC_DESCR=docname)
    
    if debug: print ('##\n## RETRIEVE IMAGE REQUEST\n##\n%s\n' % data)

    r = requests.post(hosted_scan_service.ep_ref_addr, headers=headers, data=data)

    content_with_header = b'Content-type: ' + r.headers['Content-Type'].encode('ascii') + r.content
    m = email.message_from_bytes(content_with_header)

    l = list(m.walk())

    if debug: print ('##\n## RETRIEVE IMAGE RESPONSE\n##\n%s\n' % l[1])
    open(docname, "wb").write(l[2].get_payload(decode=True))


def WSD_CancelJob(hosted_scan_service, job):
    data = messageFromFile(AbsPath("../templates/ws-scan_retrieveimage.xml"),
                       FROM=urn,
                       TO=hosted_scan_service.ep_ref_addr,
                       JOB_ID=job.id)

    if debug: print ('##\n## CANCEL JOB REQUEST\n##\n%s\n' % data)
    r = requests.post(hosted_scan_service.ep_ref_addr, headers=headers, data=data)

    x = etree.fromstring(r.text)
    if debug: print ('##\n## CANCEL JOB RESPONSE\n##\n')
    if debug: print (etree.tostring(x, pretty_print=True, xml_declaration=True).decode('ascii'))

    x.find(".//sca:ClientErrorJobIdNotFound", NSMAP)
    return (x is None)

def WSD_GetJobElements(hosted_scan_service, job):
    pass

def WSD_GetActiveJobs(hosted_scan_service):
    pass

def WSD_GetJobHistory(hosted_Scan_service):
    pass

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
                print(sc)
                (valid, ticket) = WSD_ValidateScanTicket(b, sc.std_ticket)
                if valid:
                    j = WSD_CreateScanJob(b, ticket)
                    print (j)
                    WSD_RetrieveImage(b,j, "test.jpeg")
