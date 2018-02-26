#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import wsd_discovery
from wsd_structures import *


def wsd_get(target_service):
    """
    Query wsd target for information about model/device and hosted services.

    :param target_service: A wsd target
    :return: A tuple containing a TargetInfo and a list of HostedService instances.
    """
    fields = {"FROM": urn,
              "TO": target_service.ep_ref_addr}
    x = submit_request(target_service.xaddrs[0],
                       "ws-transfer_get.xml",
                       fields,
                       "GET")

    meta = xml_find(x, ".//mex:Metadata")
    meta_model = xml_find(meta,
                          ".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisModel']")
    meta_dev = xml_find(meta,
                        ".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/ThisDevice']")
    meta_rel = xml_find(meta,
                        ".//mex:MetadataSection[@Dialect='http://schemas.xmlsoap.org/ws/2006/02/devprof/Relationship']")

    tinfo = TargetInfo()
    # WSD-Profiles section 5.1 (+ PNP-X)
    tinfo.manufacturer = xml_find(meta_model, ".//wsdp:Manufacturer").text
    tinfo.manufacturer_url = xml_find(meta_model, ".//wsdp:ManufacturerUrl").text
    tinfo.model_name = xml_find(meta_model, ".//wsdp:ModelName").text
    tinfo.model_number = xml_find(meta_model, ".//wsdp:ModelNumber").text
    tinfo.model_url = xml_find(meta_model, ".//wsdp:ModelUrl").text
    tinfo.presentation_url = xml_find(meta_model, ".//wsdp:PresentationUrl").text
    tinfo.device_cat = xml_find(meta_model, ".//pnpx:DeviceCategory").text.split()

    tinfo.friendly_name = xml_find(meta_dev, ".//wsdp:FriendlyName").text
    tinfo.fw_ver = xml_find(meta_dev, ".//wsdp:FirmwareVersion").text
    tinfo.serial_num = xml_find(meta_dev, ".//wsdp:SerialNumber").text

    hservices = []
    # WSD-Profiles section 5.2 (+ PNP-X)
    xml_findall(meta_rel, ".//wsdp:Relationship[@Type='http://schemas.xmlsoap.org/ws/2006/02/devprof/host']")

    for r in meta_rel:
        # UNCLEAR how the host item should differ from the target endpoint, and how to manage multiple host items
        # TBD - need some real-case examples
        # host = xml_find(r, ".//wsdp:Host")
        # if host is not None:    #"if omitted, implies the same endpoint reference of the targeted service"
        #    xml_find(host, ".//wsdp:Types").text
        #    xml_find(host, ".//wsdp:ServiceId").text
        #    er = xml_find(host, ".//wsa:EndpointReference")
        #    xml_find(er, ".//wsa:Address").text  #Optional endpoint fields not implemented yet
        hosted = xml_findall(r, ".//wsdp:Hosted")
        for h in hosted:
            hs = HostedService()
            hs.types = xml_find(h, ".//wsdp:Types").text.split()
            hs.service_id = xml_find(h, ".//wsdp:ServiceId").text
            hs.hardware_id = xml_find(h, ".//pnpx:HardwareId").text
            hs.compatible_id = xml_find(h, ".//pnpx:CompatibleId").text
            q = xml_find(h, ".//wsdp:ServiceAddress")
            if q:
                hs.service_address = q.text
            er = xml_find(er, ".//wsa:EndpointReference")
            hs.ep_ref_addr = xml_find(er, ".//wsa:Address").text
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
