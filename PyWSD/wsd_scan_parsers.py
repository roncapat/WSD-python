#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import copy

from wsd_structures import *


def parse_scan_ticket(std_ticket):
    st = ScanTicket()
    st.job_name = xml_find(std_ticket, ".//sca:JobDescription/sca:JobName").text
    st.job_user_name = xml_find(std_ticket, ".//sca:JobDescription/sca:JobOriginatingUserName").text
    q = xml_find(std_ticket, ".//sca:JobDescription/sca:JobInformation")
    if q is not None:
        st.job_info = q.text
    dps = xml_find(std_ticket, ".//sca:DocumentParameters")
    st.doc_params = parse_document_params(dps)
    return st


def parse_media_side(ms):
    s = MediaSide()
    r = xml_find(ms, ".//sca:ScanRegion")
    if r is not None:
        q = xml_find(r, ".//sca:ScanRegionXOffset")
        if q is not None:
            s.offset = (int(q.text), s.offset[1])
        q = xml_find(r, ".//sca:ScanRegionYOffset")
        if q is not None:
            s.offset = (s.offset[0], int(q.text))
        v1 = xml_find(r, ".//sca:ScanRegionWidth")
        v2 = xml_find(r, ".//sca:ScanRegionHeight")
        s.size = (int(v1.text), int(v2.text))
    q = xml_find(ms, ".//sca:ColorProcessing")
    if q is not None:
        s.color = q.text
    q = xml_find(ms, ".//sca:Resolution/sca:Width")
    s.res = (int(q.text), s.res[1])
    q = xml_find(ms, ".//sca:Resolution/sca:Height")
    s.res = (s.res[0], int(q.text))
    return s


def parse_document_params(dps):
    dest = DocumentParams()
    q = xml_find(dps, ".//sca:Format")
    if q is not None:
        dest.format = q.text
    q = xml_find(dps, ".//sca:CompressionQualityFactor")
    if q is not None:
        dest.compression_factor = q.text
    q = xml_find(dps, ".//sca:ImagesToTransfer")
    if q is not None:
        dest.images_num = int(q.text)
    q = xml_find(dps, ".//sca:InputSource")
    if q is not None:
        dest.input_src = q.text
    q = xml_find(dps, ".//sca:ContentType")
    if q is not None:
        dest.content_type = q.text
    q = xml_find(dps, ".//sca:InputSize")
    if q is not None:
        autod = xml_find(q, ".//sca:DocumentAutoDetect")
        if autod is not None:
            dest.size_autodetect = True if autod.text == 'true' or autod.text == '1' else False
        v1 = xml_find(q, ".//sca:InputMediaSize/sca:Width")
        v2 = xml_find(q, ".//sca:InputMediaSize/sca:Height")
        dest.input_size = (int(v1.text), int(v2.text))
    q = xml_find(dps, ".//sca:Exposure")
    if q is not None:
        autod = xml_find(q, ".//sca:AutoExposure")
        if autod is not None:
            dest.auto_exposure = True if autod.text == 'true' or autod.text == '1' else False
        dest.contrast = int(xml_find(q, ".//sca:ExposureSettings/sca:Contrast").text)
        dest.brightness = int(xml_find(q, ".//sca:ExposureSettings/sca:Brightness").text)
        dest.sharpness = int(xml_find(q, ".//sca:ExposureSettings/sca:Sharpness").text)
    q = xml_find(dps, ".//sca:Scaling")
    if q is not None:
        v1 = xml_find(q, ".//sca:ScalingWidth")
        v2 = xml_find(q, ".//sca:ScalingHeight")
        dest.scaling = (int(v1.text), int(v2.text))
    q = xml_find(dps, ".//sca:Rotation")
    if q is not None:
        dest.rotation = int(q.text)
    q = xml_find(dps, ".//sca:MediaSides")
    if q is not None:
        f = xml_find(q, ".//sca:MediaFront")
        dest.front = parse_media_side(f)

        f = xml_find(q, ".//sca:MediaBack")
        if f is not None:
            dest.back = parse_media_side(f)
        else:
            dest.back = copy.deepcopy(dest.front)
    return dest


def parse_scanner_condition(scond):
    c = ScannerCondition()
    c.id = int(scond.get("Id"))
    c.time = xml_find(scond, ".//sca:Time").text
    c.name = xml_find(scond, ".//sca:Name").text
    c.component = xml_find(scond, ".//sca:Component").text
    c.severity = xml_find(scond, ".//sca:Severity").text
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


def parse_job_summary(y):
    jsum = JobSummary()
    jsum.name = xml_find(y, "sca:JobName").text
    jsum.user_name = xml_find(y, "sca:JobOriginatingUserName").text
    jsum.status = parse_job_status(y)
    return jsum


def parse_job_status(q):
    jstatus = JobStatus()
    jstatus.id = int(xml_find(q, "sca:JobId").text)
    q1 = xml_find(q, "sca:JobState")
    q2 = xml_find(q, "sca:JobCompletedState")
    jstatus.state = q1.text if q1 is not None else q2.text
    jstatus.reasons = [x.text for x in xml_findall(q, "sca:JobStateReasons")]
    jstatus.scans_completed = int(xml_find(q, "sca:ScansCompleted").text)
    a = xml_find(q, "sca:JobCreatedTime")
    jstatus.creation_time = q.text if a is not None else ""
    a = xml_find(q, "sca:JobCompletedTime")
    jstatus.completed_time = q.text if a is not None else ""
    return jstatus


def parse_scan_configuration(sca_config):
    config = ScannerConfiguration()
    ds = xml_find(sca_config, ".//sca:DeviceSettings")
    pla = xml_find(sca_config, ".//sca:Platen")
    adf = xml_find(sca_config, ".//sca:ADF")
    # .//sca:Film omitted

    s = ScannerSettings()
    q = xml_findall(ds, ".//sca:FormatsSupported/sca:FormatValue")
    s.formats = [x.text for x in q]
    v1 = xml_find(ds, ".//sca:CompressionQualityFactorSupported/sca:MinValue")
    v2 = xml_find(ds, ".//sca:CompressionQualityFactorSupported/sca:MaxValue")
    s.compression_factor = (int(v1.text), int(v2.text))
    q = xml_findall(ds, ".//sca:ContentTypesSupported/sca:ContentTypeValue")
    s.content_types = [x.text for x in q]
    q = xml_find(ds, ".//sca:DocumentSizeAutoDetectSupported")
    s.size_autodetect_sup = True if q.text == 'true' or q.text == '1' else False
    q = xml_find(ds, ".//sca:AutoExposureSupported")
    s.auto_exposure_sup = True if q.text == 'true' or q.text == '1' else False
    q = xml_find(ds, ".//sca:BrightnessSupported")
    s.brightness_sup = True if q.text == 'true' or q.text == '1' else False
    q = xml_find(ds, ".//sca:ContrastSupported")
    s.contrast_sup = True if q.text == 'true' or q.text == '1' else False
    v1 = xml_find(ds, ".//sca:ScalingRangeSupported/sca:ScalingWidth/sca:MinValue")
    v2 = xml_find(ds, ".//sca:ScalingRangeSupported/sca:ScalingWidth/sca:MaxValue")
    s.scaling_range_w = (int(v1.text), int(v2.text))
    v1 = xml_find(ds, ".//sca:ScalingRangeSupported/sca:ScalingHeight/sca:MinValue")
    v2 = xml_find(ds, ".//sca:ScalingRangeSupported/sca:ScalingHeight/sca:MaxValue")
    s.scaling_range_h = (int(v1.text), int(v2.text))
    q = xml_findall(ds, ".//sca:RotationsSupported/sca:RotationValue")
    s.rotations = [x.text for x in q]
    config.settings = s
    if pla is not None:
        config.platen = parse_scanner_source_settings(pla, "Platen")
    if adf is not None:
        q = xml_find(adf, ".//sca:ADFSupportsDuplex")
        config.adf_duplex = True if q.text == 'true' or q.text == '1' else False
        f = xml_find(adf, ".//sca:ADFFront")
        bk = xml_find(adf, ".//sca:ADFBack")
        if f is not None:
            config.front_adf = parse_scanner_source_settings(f, "ADF")
        if bk is not None:
            config.back_adf = parse_scanner_source_settings(bk, "ADF")
    return config


def parse_scan_status(sca_status):
    status = ScannerStatus()

    status.time = xml_find(sca_status, ".//sca:ScannerCurrentTime").text
    status.state = xml_find(sca_status, ".//sca:ScannerState").text
    ac = xml_find(sca_status, ".//sca:ActiveConditions")
    if ac is not None:
        dcl = xml_findall(ac, ".//sca:DeviceCondition")
        for dc in dcl:
            c = parse_scanner_condition(dc)
            status.active_conditions[c.id] = c
    q = xml_find(sca_status, ".//sca:ScannerStateReasons")
    if q is not None:
        dsr = xml_findall(q, ".//sca:ScannerStateReason")
        for sr in dsr:
            status.reasons.append(sr.text)
    q = xml_find(sca_status, ".//sca:ConditionHistory")
    if q is not None:
        chl = xml_findall(q, ".//sca:ConditionHistoryEntry")
        for che in chl:
            c = parse_scanner_condition(che)
            status.conditions_history[xml_find(che, ".//sca:ClearTime").text] = c
    return status


def parse_scan_description(sca_descr):
    description = ScannerDescription()

    description.name = xml_find(sca_descr, ".//sca:ScannerName").text
    q = xml_find(sca_descr, ".//sca:ScannerInfo")
    if q is not None:
        description.info = q.text
    q = xml_find(sca_descr, ".//sca:ScannerLocation")
    if q is not None:
        description.location = q.text
    return description


def parse_scan_job(x):
    scnj = ScanJob()
    scnj.id = int(xml_find(x, ".//sca:JobId").text)
    scnj.token = xml_find(x, ".//sca:JobToken").text
    q = xml_find(x, ".//sca:ImageInformation/sca:MediaFrontImageInfo")
    scnj.f_pixel_line = int(xml_find(q, "sca:PixelsPerLine").text)
    scnj.f_num_lines = int(xml_find(q, "sca:NumberOfLines").text)
    scnj.f_byte_line = int(xml_find(q, "sca:BytesPerLine").text)
    q = xml_find(x, ".//sca:ImageInformation/sca:MediaBackImageInfo")
    if q is not None:
        scnj.b_pixel_line = int(xml_find(q, "sca:PixelsPerLine").text)
        scnj.b_num_lines = int(xml_find(q, "sca:NumberOfLines").text)
        scnj.b_byte_line = int(xml_find(q, "sca:BytesPerLine").text)
    dpf = xml_find(x, ".//sca:DocumentFinalParameters")
    scnj.doc_params = parse_document_params(dpf)
    return scnj
