#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import email

import wsd_discovery
import wsd_transfer
from wsd_scan_parsers import *

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
         "wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
         "sca": "http://schemas.microsoft.com/windows/2006/08/wdp/scan"}


def wsd_get_scanner_elements(hosted_scan_service):
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_getscannerelements.xml",
                       fields,
                       "GET SCANNER ELEMENTS")

    re = x.find(".//sca:ScannerElements", NSMAP)
    sca_status = re.find(".//sca:ScannerStatus", NSMAP)
    sca_config = re.find(".//sca:ScannerConfiguration", NSMAP)
    sca_descr = re.find(".//sca:ScannerDescription", NSMAP)
    std_ticket = re.find(".//sca:DefaultScanTicket", NSMAP)

    scs = ScannerService()

    scs.name = sca_descr.find(".//sca:ScannerName", NSMAP).text
    q = sca_descr.find(".//sca:ScannerInfo", NSMAP)
    if q is not None:
        scs.info = q.text
    q = sca_descr.find(".//sca:ScannerLocation", NSMAP)
    if q is not None:
        scs.location = q.text

    scs.status.time = sca_status.find(".//sca:ScannerCurrentTime", NSMAP).text
    scs.status.state = sca_status.find(".//sca:ScannerState", NSMAP).text
    ac = sca_status.find(".//sca:ActiveConditions", NSMAP)
    if ac is not None:
        dcl = ac.findall(".//sca:DeviceCondition", NSMAP)
        for dc in dcl:
            c = parse_scanner_condition(dc)
            scs.status.active_conditions.append(c)
    q = sca_status.find(".//sca:ScannerStateReasons", NSMAP)
    if q is not None:
        dsr = q.findall(".//sca:ScannerStateReason", NSMAP)
        for sr in dsr:
            scs.status.reasons.append(sr.text)
    q = sca_status.find(".//sca:ConditionHistory", NSMAP)
    if q is not None:
        chl = q.findall(".//sca:ConditionHistoryEntry", NSMAP)
        for che in chl:
            c = parse_scanner_condition(che)
            scs.status.conditions_history.append((che.find(".//sca:ClearTime", NSMAP).text, c))

    ds = sca_config.find(".//sca:DeviceSettings", NSMAP)
    pla = sca_config.find(".//sca:Platen", NSMAP)
    adf = sca_config.find(".//sca:ADF", NSMAP)
    # .//sca:Film omitted

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
    scs.settings = s
    if pla is not None:
        scs.platen = parse_scanner_source_settings(pla, "Platen")
    if adf is not None:
        q = adf.find(".//sca:ADFSupportsDuplex", NSMAP)
        scs.adf_duplex = True if q.text == 'true' or q.text == '1' else False
        f = adf.find(".//sca:ADFFront", NSMAP)
        bk = adf.find(".//sca:ADFBack", NSMAP)
        if f is not None:
            scs.front_adf = parse_scanner_source_settings(f, "ADF")
        if bk is not None:
            scs.back_adf = parse_scanner_source_settings(bk, "ADF")

    scs.std_ticket = parse_scan_ticket(std_ticket)

    return scs


def wsd_validate_scan_ticket(hosted_scan_service, tkt):
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_validatescanticket.xml",
                       {**fields, **tkt.as_map()},
                       "VALIDATE SCAN TICKET")

    v = x.find(".//sca:ValidTicket", NSMAP)
    is_valid = True if v.text == 'true' or v.text == '1' else False
    if is_valid:
        return True, tkt
    else:
        return False, parse_scan_ticket(x.find(".//sca::ValidScanTicket", NSMAP))


def wsd_create_scan_job(hosted_scan_service, tkt, scan_identifier="", dest_token=""):
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "SCAN_ID": scan_identifier,
              "DEST_TOKEN": dest_token}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_createscanjob.xml",
                       {**fields, **tkt.as_map()},
                       "CREATE SCAN JOB")

    scnj = ScanJob()
    x = x.find(".//sca:CreateScanJobResponse", NSMAP)
    scnj.id = int(x.find(".//sca:JobId", NSMAP).text)
    scnj.token = x.find(".//sca:JobToken", NSMAP).text
    q = x.find(".//sca:ImageInformation/sca:MediaFrontImageInfo", NSMAP)
    scnj.f_pixel_line = int(q.find("sca:PixelsPerLine", NSMAP).text)
    scnj.f_num_lines = int(q.find("sca:NumberOfLines", NSMAP).text)
    scnj.f_byte_line = int(q.find("sca:BytesPerLine", NSMAP).text)
    q = x.find(".//sca:ImageInformation/sca:MediaBackImageInfo", NSMAP)
    if q is not None:
        scnj.b_pixel_line = int(q.find("sca:PixelsPerLine", NSMAP).text)
        scnj.b_num_lines = int(q.find("sca:NumberOfLines", NSMAP).text)
        scnj.b_byte_line = int(q.find("sca:BytesPerLine", NSMAP).text)
    dpf = x.find(".//sca:DocumentFinalParameters", NSMAP)
    scnj.doc_params = parse_document_params(dpf)

    return scnj


def wsd_retrieve_image(hosted_scan_service, job, docname):
    data = message_from_file(abs_path("../templates/ws-scan_retrieveimage.xml"),
                             FROM=urn,
                             TO=hosted_scan_service.ep_ref_addr,
                             JOB_ID=job.id,
                             JOB_TOKEN=job.token,
                             DOC_DESCR=docname)

    if debug:
        print('##\n## RETRIEVE IMAGE REQUEST\n##\n%s\n' % data)

    r = requests.post(hosted_scan_service.ep_ref_addr, headers=headers, data=data)

    try:
        x = etree.fromstring(r.text)
        q = x.find(".//soap:Fault", NSMAP)
        if q is not None:
            e = q.find(".//soap:Code/soap:Subcode/soap:Value", NSMAP).text
            if e == "wscn:ClientErrorNoImagesAvailable":
                return False
    except:
        content_with_header = b'Content-type: ' + r.headers['Content-Type'].encode('ascii') + r.content
        m = email.message_from_bytes(content_with_header)

        ls = list(m.walk())

        if debug:
            print('##\n## RETRIEVE IMAGE RESPONSE\n##\n%s\n' % ls[1])
        open(docname, "wb").write(ls[2].get_payload(decode=True))

        return True


def wsd_cancel_job(hosted_scan_service, job):
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "JOB_ID": job.id}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_canceljob.xml",
                       fields,
                       "CANCEL JOB")

    x.find(".//sca:ClientErrorJobIdNotFound", NSMAP)
    return x is None


def wsd_get_job_elements(hosted_scan_service, job):
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "JOB_ID": job.id}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_getjobelements.xml",
                       fields,
                       "GET JOB ELEMENTS")

    q = x.find(".//sca:JobStatus", NSMAP)
    jstatus = parse_job_status(q)

    st = x.find(".//sca:ScanTicket", NSMAP)
    tkt = parse_scan_ticket(st)

    ds = x.find(".//sca:Documents", NSMAP)
    dfp = ds.find("sca:DocumentFinalParameters", NSMAP)
    dps = parse_document_params(dfp)
    dlist = [x.text for x in dfp.findall("sca:Document/sca:DocumentDescription/sca:DocumentName", NSMAP)]

    return jstatus, tkt, dps, dlist


def wsd_get_active_jobs(hosted_scan_service):
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_getactivejobs.xml",
                       fields,
                       "GET ACTIVE JOBS")

    jsl = []
    for y in x.findall(".//sca:JobSummary", NSMAP):
        jsum = JobSummary()
        jsum.name = y.find("sca:JobName", NSMAP).text
        jsum.user_name = y.find("sca:JobOriginatingUserName", NSMAP).text
        jsum.status = parse_job_status(y)
        jsl.append(jsum)

    return jsl


def wsd_get_job_history(hosted_scan_service):
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_getjobhistory.xml",
                       fields,
                       "GET JOB HISTORY")

    jsl = []
    for y in x.findall(".//sca:JobSummary", NSMAP):
        jsum = JobSummary()
        jsum.name = y.find("sca:JobName", NSMAP).text
        jsum.user_name = y.find("sca:JobOriginatingUserName", NSMAP).text
        jsum.status = parse_job_status(y)
        jsl.append(jsum)

    return jsl


if __name__ == "__main__":
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    tsl = wsd_discovery.get_devices()
    for a in tsl:
        (ti, hss) = wsd_transfer.wsd_get(a)
        for b in hss:
            if "wscn:ScannerServiceType" in b.types:
                sc = wsd_get_scanner_elements(b)
                print(a)
                print(ti)
                print(b)
                print(sc)
                t = sc.std_ticket
                # t.doc_params.input_src = "ADF"
                # t.doc_params.images_num = 0
                (valid, ticket) = wsd_validate_scan_ticket(b, t)
                if valid:
                    j = wsd_create_scan_job(b, ticket)
                    print(j)
                    (js, t, dp, dl) = wsd_get_job_elements(b, j)
                    print(js)
                    print(t)
                    print(dp)
                    print(dl)
                    jobs = wsd_get_active_jobs(b)
                    for i in jobs:
                        print(i)
                    jobs = wsd_get_job_history(b)
                    for i in jobs:
                        print(i)
                    o = 0
                    while wsd_retrieve_image(b, j, "test_%d.jpeg" % o):
                        o = o + 1
