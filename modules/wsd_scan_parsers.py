#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import copy

from wsd_structures import *

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
         "wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
         "sca": "http://schemas.microsoft.com/windows/2006/08/wdp/scan"}


def parse_scan_ticket(std_ticket):
    st = ScanTicket()
    st.job_name = std_ticket.find(".//sca:JobDescription/sca:JobName", NSMAP).text
    st.job_user_name = std_ticket.find(".//sca:JobDescription/sca:JobOriginatingUserName", NSMAP).text
    q = std_ticket.find(".//sca:JobDescription/sca:JobInformation", NSMAP)
    if q is not None:
        st.job_info = q.text
    dps = std_ticket.find(".//sca:DocumentParameters", NSMAP)
    st.doc_params = parse_document_params(dps)
    return st


def parse_media_side(ms):
    s = MediaSide()
    r = ms.find(".//sca:ScanRegion", NSMAP)
    if r is not None:
        q = r.find(".//sca:ScanRegionXOffset", NSMAP)
        if q is not None:
            s.offset = (int(q.text), s.offset[1])
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
    s.res = (int(q.text), s.res[1])
    q = ms.find(".//sca:Resolution/sca:Height", NSMAP)
    s.res = (s.res[0], int(q.text))
    return s


def parse_document_params(dps):
    dest = DocumentParams()
    q = dps.find(".//sca:Format", NSMAP)
    if q is not None:
        dest.format = q.text
    q = dps.find(".//sca:CompressionQualityFactor", NSMAP)
    if q is not None:
        dest.compression_factor = q.text
    q = dps.find(".//sca:ImagesToTransfer", NSMAP)
    if q is not None:
        dest.images_num = int(q.text)
    q = dps.find(".//sca:InputSource", NSMAP)
    if q is not None:
        dest.input_src = q.text
    q = dps.find(".//sca:ContentType", NSMAP)
    if q is not None:
        dest.content_type = q.text
    q = dps.find(".//sca:InputSize", NSMAP)
    if q is not None:
        autod = q.find(".//sca:DocumentAutoDetect", NSMAP)
        if autod is not None:
            dest.size_autodetect = True if autod.text == 'true' or autod.text == '1' else False
        v1 = q.find(".//sca:InputMediaSize/sca:Width", NSMAP)
        v2 = q.find(".//sca:InputMediaSize/sca:Height", NSMAP)
        dest.input_size = (int(v1.text), int(v2.text))
    q = dps.find(".//sca:Exposure", NSMAP)
    if q is not None:
        autod = q.find(".//sca:AutoExposure", NSMAP)
        if autod is not None:
            dest.auto_exposure = True if autod.text == 'true' or autod.text == '1' else False
        dest.contrast = int(q.find(".//sca:ExposureSettings/sca:Contrast", NSMAP).text)
        dest.brightness = int(q.find(".//sca:ExposureSettings/sca:Brightness", NSMAP).text)
        dest.sharpness = int(q.find(".//sca:ExposureSettings/sca:Sharpness", NSMAP).text)
    q = dps.find(".//sca:Scaling", NSMAP)
    if q is not None:
        v1 = q.find(".//sca:ScalingWidth", NSMAP)
        v2 = q.find(".//sca:ScalingHeight", NSMAP)
        dest.scaling = (int(v1.text), int(v2.text))
    q = dps.find(".//sca:Rotation", NSMAP)
    if q is not None:
        dest.rotation = int(q.text)
    q = dps.find(".//sca:MediaSides", NSMAP)
    if q is not None:
        f = q.find(".//sca:MediaFront", NSMAP)
        dest.front = parse_media_side(f)

        f = q.find(".//sca:MediaBack", NSMAP)
        if f is not None:
            dest.back = parse_media_side(f)
        else:
            dest.back = copy.deepcopy(dest.front)
    return dest


def parse_scanner_condition(scond):
    c = ScannerCondition()
    c.id = int(scond.get("Id"))
    c.time = scond.find(".//sca:Time", NSMAP).text
    c.name = scond.find(".//sca:Name", NSMAP).text
    c.component = scond.find(".//sca:Component", NSMAP).text
    c.severity = scond.find(".//sca:Severity", NSMAP).text
    return c


def parse_scanner_source_settings(se, name):
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


def parse_job_status(q):
    jstatus = JobStatus()
    jstatus.id = int(q.find("sca:JobId", NSMAP).text)
    jstatus.state = q.find("sca:JobState", NSMAP).text
    jstatus.reasons = [x.text for x in q.findall("sca:JobStateReasons", NSMAP)]
    jstatus.scans_completed = int(q.find("sca:ScansCompleted", NSMAP).text)
    a = q.find("sca:JobCreatedTime", NSMAP)
    jstatus.creation_time = q.text if a is not None else ""
    a = q.find("sca:JobCompletedTime", NSMAP)
    jstatus.completed_time = q.text if a is not None else ""
    return jstatus


def parse_scan_configuration(sca_config):
    config = ScannerConfiguration()
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
    config.settings = s
    if pla is not None:
        config.platen = parse_scanner_source_settings(pla, "Platen")
    if adf is not None:
        q = adf.find(".//sca:ADFSupportsDuplex", NSMAP)
        config.adf_duplex = True if q.text == 'true' or q.text == '1' else False
        f = adf.find(".//sca:ADFFront", NSMAP)
        bk = adf.find(".//sca:ADFBack", NSMAP)
        if f is not None:
            config.front_adf = parse_scanner_source_settings(f, "ADF")
        if bk is not None:
            config.back_adf = parse_scanner_source_settings(bk, "ADF")
    return config


def parse_scan_status(sca_status):
    status = ScannerStatus()

    status.time = sca_status.find(".//sca:ScannerCurrentTime", NSMAP).text
    status.state = sca_status.find(".//sca:ScannerState", NSMAP).text
    ac = sca_status.find(".//sca:ActiveConditions", NSMAP)
    if ac is not None:
        dcl = ac.findall(".//sca:DeviceCondition", NSMAP)
        for dc in dcl:
            c = parse_scanner_condition(dc)
            status.active_conditions[c.id] = c
    q = sca_status.find(".//sca:ScannerStateReasons", NSMAP)
    if q is not None:
        dsr = q.findall(".//sca:ScannerStateReason", NSMAP)
        for sr in dsr:
            status.reasons.append(sr.text)
    q = sca_status.find(".//sca:ConditionHistory", NSMAP)
    if q is not None:
        chl = q.findall(".//sca:ConditionHistoryEntry", NSMAP)
        for che in chl:
            c = parse_scanner_condition(che)
            status.conditions_history[che.find(".//sca:ClearTime", NSMAP).text] = c
    return status


def parse_scan_description(sca_descr):
    description = ScannerDescription()

    description.name = sca_descr.find(".//sca:ScannerName", NSMAP).text
    q = sca_descr.find(".//sca:ScannerInfo", NSMAP)
    if q is not None:
        description.info = q.text
    q = sca_descr.find(".//sca:ScannerLocation", NSMAP)
    if q is not None:
        description.location = q.text
    return description
