#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import wsd_discovery
from wsd_structures import *

NSMAP = {"soap": "http://www.w3.org/2003/05/soap-envelope",
         "wsa": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
         "mex": "http://schemas.xmlsoap.org/ws/2004/09/mex",
         "wsdp": "http://schemas.xmlsoap.org/ws/2006/02/devprof",
         "wprt": "http://schemas.microsoft.com/windows/2006/08/wdp/print",
         "wscn": 'http://schemas.microsoft.com/windows/2006/08/wdp/scan',
         'pnpx': "http://schemas.microsoft.com/windows/pnpx/2005/10",
         "df": "http://schemas.microsoft.com/windows/2008/09/devicefoundation"}


def wsd_get(target_service):
    '''
    Query wsd target for information about model/device and hosted services.

    :param target_service: A wsd target
    :return: A tuple containing a TargetInfo and a list of HostedService instances.
    '''
    fields = {"FROM": urn,
              "TO": target_service.ep_ref_addr}
    x = submit_request(target_service.xaddrs[0],
                      "ws-transfer_get.xml",
                       fields,
                      "GET")

    meta = x.find(".//mex:Metadata", NSMAP)
    meta_model = meta.find(
        ".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisModel']",
        NSMAP)
    meta_dev = meta.find(
        ".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisDevice']",
        NSMAP)
    meta_rel = meta.find(
        ".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/Relationship']",
        NSMAP)

    tinfo = TargetInfo()
    # WSD-Profiles section 5.1 (+ PNP-X)
    tinfo.manufacturer = meta_model.find(".//wsdp:Manufacturer", NSMAP).text
    tinfo.manufacturer_url = meta_model.find(".//wsdp:ManufacturerUrl", NSMAP).text
    tinfo.model_name = meta_model.find(".//wsdp:ModelName", NSMAP).text
    tinfo.model_number = meta_model.find(".//wsdp:ModelNumber", NSMAP).text
    tinfo.model_url = meta_model.find(".//wsdp:ModelUrl", NSMAP).text
    tinfo.presentation_url = meta_model.find(".//wsdp:PresentationUrl", NSMAP).text
    tinfo.device_cat = meta_model.find(".//pnpx:DeviceCategory", NSMAP).text.split()

    tinfo.friendly_name = meta_dev.find(".//wsdp:FriendlyName", NSMAP).text
    tinfo.fw_ver = meta_dev.find(".//wsdp:FirmwareVersion", NSMAP).text
    tinfo.serial_num = meta_dev.find(".//wsdp:SerialNumber", NSMAP).text

    hservices = []
    # WSD-Profiles section 5.2 (+ PNP-X)
    meta_rel.findall(".//wsdp:Relationship[@Type='http://schemas.xmlsoap.org/ws/2006/02/devprof/host']", NSMAP)
    for r in meta_rel:
        # UNCLEAR how the host item should differ from the target endpoint, and how to manage multiple host items
        # TBD - need some real-case examples
        # host = r.find(".//wsdp:Host", NSMAP)
        # if host:    #"if omitted, implies the same endpoint reference of the targeted service"
        #    host.find(".//wsdp:Types", NSMAP).text 
        #    host.find(".//wsdp:ServiceId", NSMAP).text 
        #    er = host.find(".//wsa:EndpointReference", NSMAP)
        #    er.find(".//wsa:Address", NSMAP).text  #Optional endpoint fields not implemented yet
        hosted = r.findall(".//wsdp:Hosted", NSMAP)
        for h in hosted:
            hs = HostedService()
            hs.types = h.find(".//wsdp:Types", NSMAP).text.split()
            hs.service_id = h.find(".//wsdp:ServiceId", NSMAP).text
            hs.hardware_id = h.find(".//pnpx:HardwareId", NSMAP).text
            hs.compatible_id = h.find(".//pnpx:CompatibleId", NSMAP).text
            q = h.find(".//wsdp:ServiceAddress", NSMAP)
            if q:
                hs.service_address = q.text
            er = h.find(".//wsa:EndpointReference", NSMAP)
            hs.ep_ref_addr = er.find(".//wsa:Address", NSMAP).text
            hservices.append(hs)

    # WSD-Profiles section 5.3 and 5.4 omitted
    return tinfo, hservices


if __name__ == "__main__":
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    tsl = wsd_discovery.get_devices()
    for a in tsl:
        print(a)
        (ti, hss) = wsd_get(a)
        print(ti)
        for b in hss:
            print(b)
