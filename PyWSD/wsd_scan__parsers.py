#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import copy

import wsd_common
import wsd_scan__structures


# TODO: use declxml https://github.com/gatkin/declxml
# NB: declxml do not support namespaces AFAIK

def parse_scan_ticket(std_ticket):
    st = wsd_scan__structures.ScanTicket()
    st.job_name = wsd_common.xml_find(std_ticket, ".//sca:JobDescription/sca:JobName").text
    st.job_user_name = wsd_common.xml_find(std_ticket, ".//sca:JobDescription/sca:JobOriginatingUserName").text
    q = wsd_common.xml_find(std_ticket, ".//sca:JobDescription/sca:JobInformation")
    if q is not None:
        st.job_info = q.text
    dps = wsd_common.xml_find(std_ticket, ".//sca:DocumentParameters")
    st.doc_params = parse_document_params(dps)
    return st


def parse_media_side(ms):
    s = wsd_scan__structures.MediaSide()
    r = wsd_common.xml_find(ms, ".//sca:ScanRegion")
    if r is not None:
        q = wsd_common.xml_find(r, ".//sca:ScanRegionXOffset")
        if q is not None:
            s.offset = (int(q.text), s.offset[1])
        q = wsd_common.xml_find(r, ".//sca:ScanRegionYOffset")
        if q is not None:
            s.offset = (s.offset[0], int(q.text))
        v1 = wsd_common.xml_find(r, ".//sca:ScanRegionWidth")
        v2 = wsd_common.xml_find(r, ".//sca:ScanRegionHeight")
        s.size = (int(v1.text), int(v2.text))
    q = wsd_common.xml_find(ms, ".//sca:ColorProcessing")
    if q is not None:
        s.color = q.text
    q = wsd_common.xml_find(ms, ".//sca:Resolution/sca:Width")
    s.res = (int(q.text), s.res[1])
    q = wsd_common.xml_find(ms, ".//sca:Resolution/sca:Height")
    s.res = (s.res[0], int(q.text))
    return s


def parse_document_params(dps):
    dest = wsd_scan__structures.DocumentParams()
    q = wsd_common.xml_find(dps, ".//sca:Format")
    if q is not None:
        dest.format = q.text
    q = wsd_common.xml_find(dps, ".//sca:CompressionQualityFactor")
    if q is not None:
        dest.compression_factor = q.text
    q = wsd_common.xml_find(dps, ".//sca:ImagesToTransfer")
    if q is not None:
        dest.images_num = int(q.text)
    q = wsd_common.xml_find(dps, ".//sca:InputSource")
    if q is not None:
        dest.input_src = q.text
    q = wsd_common.xml_find(dps, ".//sca:ContentType")
    if q is not None:
        dest.content_type = q.text
    q = wsd_common.xml_find(dps, ".//sca:InputSize")
    if q is not None:
        autod = wsd_common.xml_find(q, ".//sca:DocumentAutoDetect")
        if autod is not None:
            dest.size_autodetect = True if autod.text == 'true' or autod.text == '1' else False
        v1 = wsd_common.xml_find(q, ".//sca:InputMediaSize/sca:Width")
        v2 = wsd_common.xml_find(q, ".//sca:InputMediaSize/sca:Height")
        dest.input_size = (int(v1.text), int(v2.text))
    q = wsd_common.xml_find(dps, ".//sca:Exposure")
    if q is not None:
        autod = wsd_common.xml_find(q, ".//sca:AutoExposure")
        if autod is not None:
            dest.auto_exposure = True if autod.text == 'true' or autod.text == '1' else False
        dest.contrast = int(wsd_common.xml_find(q, ".//sca:ExposureSettings/sca:Contrast").text)
        dest.brightness = int(wsd_common.xml_find(q, ".//sca:ExposureSettings/sca:Brightness").text)
        dest.sharpness = int(wsd_common.xml_find(q, ".//sca:ExposureSettings/sca:Sharpness").text)
    q = wsd_common.xml_find(dps, ".//sca:Scaling")
    if q is not None:
        v1 = wsd_common.xml_find(q, ".//sca:ScalingWidth")
        v2 = wsd_common.xml_find(q, ".//sca:ScalingHeight")
        dest.scaling = (int(v1.text), int(v2.text))
    q = wsd_common.xml_find(dps, ".//sca:Rotation")
    if q is not None:
        dest.rotation = int(q.text)
    q = wsd_common.xml_find(dps, ".//sca:MediaSides")
    if q is not None:
        f = wsd_common.xml_find(q, ".//sca:MediaFront")
        dest.front = parse_media_side(f)

        f = wsd_common.xml_find(q, ".//sca:MediaBack")
        if f is not None:
            dest.back = parse_media_side(f)
        else:
            dest.back = copy.deepcopy(dest.front)
    return dest


def parse_scanner_condition(scond):
    c = wsd_scan__structures.ScannerCondition()
    c.id = int(scond.get("Id"))
    c.time = wsd_common.xml_find(scond, ".//sca:Time").text
    c.name = wsd_common.xml_find(scond, ".//sca:Name").text
    c.component = wsd_common.xml_find(scond, ".//sca:Component").text
    c.severity = wsd_common.xml_find(scond, ".//sca:Severity").text
    return c


def parse_scanner_source_settings(se, name):
    sss = wsd_scan__structures.ScannerSourceSettings()
    v1 = wsd_common.xml_find(se, ".//sca:%sOpticalResolution/sca:Width" % name)
    v2 = wsd_common.xml_find(se, ".//sca:%sOpticalResolution/sca:Height" % name)
    sss.optical_res = (int(v1.text), int(v2.text))
    q = wsd_common.xml_findall(se, ".//sca:%sResolutions/sca:Widths/sca:Width" % name)
    sss.width_res = [x.text for x in q]
    q = wsd_common.xml_findall(se, ".//sca:%sResolutions/sca:Heights/sca:Height" % name)
    sss.height_res = [x.text for x in q]
    q = wsd_common.xml_findall(se, ".//sca:%sColor/sca:ColorEntry" % name)
    sss.color_modes = [x.text for x in q]
    v1 = wsd_common.xml_find(se, ".//sca:%sMinimumSize/sca:Width" % name)
    v2 = wsd_common.xml_find(se, ".//sca:%sMinimumSize/sca:Height" % name)
    sss.min_size = (int(v1.text), int(v2.text))
    v1 = wsd_common.xml_find(se, ".//sca:%sMaximumSize/sca:Width" % name)
    v2 = wsd_common.xml_find(se, ".//sca:%sMaximumSize/sca:Height" % name)
    sss.max_size = (int(v1.text), int(v2.text))
    return sss


def parse_job_summary(y):
    jsum = wsd_scan__structures.JobSummary()
    jsum.name = wsd_common.xml_find(y, "sca:JobName").text
    jsum.user_name = wsd_common.xml_find(y, "sca:JobOriginatingUserName").text
    jsum.status = parse_job_status(y)
    return jsum


def parse_job_status(q):
    jstatus = wsd_scan__structures.JobStatus()
    jstatus.id = int(wsd_common.xml_find(q, "sca:JobId").text)
    q1 = wsd_common.xml_find(q, "sca:JobState")
    q2 = wsd_common.xml_find(q, "sca:JobCompletedState")
    jstatus.state = q1.text if q1 is not None else q2.text
    jstatus.reasons = [x.text for x in wsd_common.xml_findall(q, "sca:JobStateReasons")]
    jstatus.scans_completed = int(wsd_common.xml_find(q, "sca:ScansCompleted").text)
    a = wsd_common.xml_find(q, "sca:JobCreatedTime")
    jstatus.creation_time = q.text if a is not None else ""
    a = wsd_common.xml_find(q, "sca:JobCompletedTime")
    jstatus.completed_time = q.text if a is not None else ""
    return jstatus


def parse_scan_configuration(sca_config):
    config = wsd_scan__structures.ScannerConfiguration()
    ds = wsd_common.xml_find(sca_config, ".//sca:DeviceSettings")
    pla = wsd_common.xml_find(sca_config, ".//sca:Platen")
    adf = wsd_common.xml_find(sca_config, ".//sca:ADF")
    # .//sca:Film omitted

    s = wsd_scan__structures.ScannerSettings()
    q = wsd_common.xml_findall(ds, ".//sca:FormatsSupported/sca:FormatValue")
    s.formats = [x.text for x in q]
    v1 = wsd_common.xml_find(ds, ".//sca:CompressionQualityFactorSupported/sca:MinValue")
    v2 = wsd_common.xml_find(ds, ".//sca:CompressionQualityFactorSupported/sca:MaxValue")
    s.compression_factor = (int(v1.text), int(v2.text))
    q = wsd_common.xml_findall(ds, ".//sca:ContentTypesSupported/sca:ContentTypeValue")
    s.content_types = [x.text for x in q]
    q = wsd_common.xml_find(ds, ".//sca:DocumentSizeAutoDetectSupported")
    s.size_autodetect_sup = True if q.text == 'true' or q.text == '1' else False
    q = wsd_common.xml_find(ds, ".//sca:AutoExposureSupported")
    s.auto_exposure_sup = True if q.text == 'true' or q.text == '1' else False
    q = wsd_common.xml_find(ds, ".//sca:BrightnessSupported")
    s.brightness_sup = True if q.text == 'true' or q.text == '1' else False
    q = wsd_common.xml_find(ds, ".//sca:ContrastSupported")
    s.contrast_sup = True if q.text == 'true' or q.text == '1' else False
    v1 = wsd_common.xml_find(ds, ".//sca:ScalingRangeSupported/sca:ScalingWidth/sca:MinValue")
    v2 = wsd_common.xml_find(ds, ".//sca:ScalingRangeSupported/sca:ScalingWidth/sca:MaxValue")
    s.scaling_range_w = (int(v1.text), int(v2.text))
    v1 = wsd_common.xml_find(ds, ".//sca:ScalingRangeSupported/sca:ScalingHeight/sca:MinValue")
    v2 = wsd_common.xml_find(ds, ".//sca:ScalingRangeSupported/sca:ScalingHeight/sca:MaxValue")
    s.scaling_range_h = (int(v1.text), int(v2.text))
    q = wsd_common.xml_findall(ds, ".//sca:RotationsSupported/sca:RotationValue")
    s.rotations = [x.text for x in q]
    config.settings = s
    if pla is not None:
        config.platen = parse_scanner_source_settings(pla, "Platen")
    if adf is not None:
        q = wsd_common.xml_find(adf, ".//sca:ADFSupportsDuplex")
        config.adf_duplex = True if q.text == 'true' or q.text == '1' else False
        f = wsd_common.xml_find(adf, ".//sca:ADFFront")
        bk = wsd_common.xml_find(adf, ".//sca:ADFBack")
        if f is not None:
            config.front_adf = parse_scanner_source_settings(f, "ADF")
        if bk is not None:
            config.back_adf = parse_scanner_source_settings(bk, "ADF")
    return config


def parse_scan_status(sca_status):
    status = wsd_scan__structures.ScannerStatus()

    status.time = wsd_common.xml_find(sca_status, ".//sca:ScannerCurrentTime").text
    status.state = wsd_common.xml_find(sca_status, ".//sca:ScannerState").text
    ac = wsd_common.xml_find(sca_status, ".//sca:ActiveConditions")
    if ac is not None:
        dcl = wsd_common.xml_findall(ac, ".//sca:DeviceCondition")
        for dc in dcl:
            c = parse_scanner_condition(dc)
            status.active_conditions[c.id] = c
    q = wsd_common.xml_find(sca_status, ".//sca:ScannerStateReasons")
    if q is not None:
        dsr = wsd_common.xml_findall(q, ".//sca:ScannerStateReason")
        for sr in dsr:
            status.reasons.append(sr.text)
    q = wsd_common.xml_find(sca_status, ".//sca:ConditionHistory")
    if q is not None:
        chl = wsd_common.xml_findall(q, ".//sca:ConditionHistoryEntry")
        for che in chl:
            c = parse_scanner_condition(che)
            status.conditions_history[wsd_common.xml_find(che, ".//sca:ClearTime").text] = c
    return status


def parse_scan_description(sca_descr):
    description = wsd_scan__structures.ScannerDescription()

    description.name = wsd_common.xml_find(sca_descr, ".//sca:ScannerName").text
    q = wsd_common.xml_find(sca_descr, ".//sca:ScannerInfo")
    if q is not None:
        description.info = q.text
    q = wsd_common.xml_find(sca_descr, ".//sca:ScannerLocation")
    if q is not None:
        description.location = q.text
    return description


def parse_scan_job(x):
    scnj = wsd_scan__structures.ScanJob()
    scnj.id = int(wsd_common.xml_find(x, ".//sca:JobId").text)
    scnj.token = wsd_common.xml_find(x, ".//sca:JobToken").text
    q = wsd_common.xml_find(x, ".//sca:ImageInformation/sca:MediaFrontImageInfo")
    scnj.f_pixel_line = int(wsd_common.xml_find(q, "sca:PixelsPerLine").text)
    scnj.f_num_lines = int(wsd_common.xml_find(q, "sca:NumberOfLines").text)
    scnj.f_byte_line = int(wsd_common.xml_find(q, "sca:BytesPerLine").text)
    q = wsd_common.xml_find(x, ".//sca:ImageInformation/sca:MediaBackImageInfo")
    if q is not None:
        scnj.b_pixel_line = int(wsd_common.xml_find(q, "sca:PixelsPerLine").text)
        scnj.b_num_lines = int(wsd_common.xml_find(q, "sca:NumberOfLines").text)
        scnj.b_byte_line = int(wsd_common.xml_find(q, "sca:BytesPerLine").text)
    dpf = wsd_common.xml_find(x, ".//sca:DocumentFinalParameters")
    scnj.doc_params = parse_document_params(dpf)
    return scnj
