#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import email
import typing
from io import BytesIO

import lxml.etree as etree
import requests
from PIL import Image, ImageSequence

from PyWSD import wsd_common, \
    wsd_discovery__operations, \
    wsd_scan__parsers, \
    wsd_scan__structures, \
    wsd_transfer__operations, \
    wsd_transfer__structures


def wsd_get_scanner_elements(hosted_scan_service: wsd_transfer__structures.HostedService):
    """
    Submit a GetScannerElements request, and parse the response.
    The device should reply with informations about itself,
    its configuration, its status and the defalt scan ticket

    :param hosted_scan_service: the wsd scan service to query
    :type hosted_scan_service: wsd_transfer__structures.HostedService
    :return: a tuple of the form (ScannerDescription, ScannerConfiguration, ScannerStatus, ScanTicket)
    """
    fields = {"FROM": wsd_common.urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = wsd_common.submit_request({hosted_scan_service.ep_ref_addr},
                                  "ws-scan__get_scanner_elements.xml",
                                  fields)

    re = wsd_common.xml_find(x, ".//sca:ScannerElements")
    sca_status = wsd_common.xml_find(re, ".//sca:ScannerStatus")
    sca_config = wsd_common.xml_find(re, ".//sca:ScannerConfiguration")
    sca_descr = wsd_common.xml_find(re, ".//sca:ScannerDescription")
    std_ticket = wsd_common.xml_find(re, ".//sca:DefaultScanTicket")

    description = wsd_scan__parsers.parse_scan_description(sca_descr)
    status = wsd_scan__parsers.parse_scan_status(sca_status)
    config = wsd_scan__parsers.parse_scan_configuration(sca_config)
    std_ticket = wsd_scan__parsers.parse_scan_ticket(std_ticket)

    return description, config, status, std_ticket


def wsd_validate_scan_ticket(hosted_scan_service: wsd_transfer__structures.HostedService,
                             tkt: wsd_scan__structures.ScanTicket) \
        -> typing.Tuple[bool, wsd_scan__structures.ScanTicket]:
    """
    Submit a ValidateScanTicket request, and parse the response.
    Scanner devices can validate scan settings/parameters and fix errors if any. It is recommended to always
    validate a ticket before submitting the actual scan job.

    :param hosted_scan_service: the wsd scan service to query
    :type hosted_scan_service: wsd_transfer__structures.HostedService
    :param tkt: the ScanTicket to submit for validation purposes
    :type tkt: wsd_scan__structures.ScanTicket
    :return: a tuple of the form (boolean, ScanTicket), where the first field is True if no errors were found during\
    validation, along with the same ticket submitted, or False if errors were found, along with a corrected ticket.
    """

    fields = {"FROM": wsd_common.urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = wsd_common.submit_request({hosted_scan_service.ep_ref_addr},
                                  "ws-scan__validate_scan_ticket.xml",
                                  {**fields, **tkt.as_map()})

    v = wsd_common.xml_find(x, ".//sca:ValidTicket")

    if v.text == 'true' or v.text == '1':
        return True, tkt
    else:
        return False, wsd_scan__parsers.parse_scan_ticket(wsd_common.xml_find(x, ".//sca::ValidScanTicket"))


def wsd_create_scan_job(hosted_scan_service: wsd_transfer__structures.HostedService,
                        tkt: wsd_scan__structures.ScanTicket,
                        scan_identifier: str = "",
                        dest_token: str = "") \
        -> wsd_scan__structures.ScanJob:
    """
    Submit a CreateScanJob request, and parse the response.
    This creates a scan job and starts the image(s) acquisition.

    :param hosted_scan_service: the wsd scan service to query
    :type hosted_scan_service: wsd_transfer__structures.HostedService
    :param tkt: the ScanTicket to submit for validation purposes
    :type tkt: wsd_scan__structures.ScanTicket
    :param scan_identifier: a string identifying the device-initiated scan to handle, if any
    :type scan_identifier: str
    :param dest_token: a token assigned by the scanner to this client, needed for device-initiated scans
    :type dest_token: str
    :return: a ScanJob instance
    :rtype: wsd_scan__structures.ScanJob
    """

    fields = {"FROM": wsd_common.urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "SCAN_ID": scan_identifier,
              "DEST_TOKEN": dest_token}
    x = wsd_common.submit_request({hosted_scan_service.ep_ref_addr},
                                  "ws-scan__create_scan_job.xml",
                                  {**fields, **tkt.as_map()})

    x = wsd_common.xml_find(x, ".//sca:CreateScanJobResponse")

    return wsd_scan__parsers.parse_scan_job(x)


def wsd_cancel_job(hosted_scan_service: wsd_transfer__structures.HostedService,
                   job: wsd_scan__structures.ScanJob) \
        -> bool:
    """
    Submit a CancelJob request, and parse the response.
    Stops and aborts the specified scan job.

    :param hosted_scan_service: the wsd scan service to query
    :type hosted_scan_service: wsd_transfer__structures.HostedService
    :param job: the ScanJob instance representing the job to abort
    :type job: wsd_scan_structures.ScanJob
    :return: True if the job is found and then aborted, False if the specified job do not exists or already ended.
    :rtype: bool
    """
    fields = {"FROM": wsd_common.urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "JOB_ID": job.id}
    x = wsd_common.submit_request({hosted_scan_service.ep_ref_addr},
                                  "ws-scan__cancel_job.xml",
                                  fields)

    wsd_common.xml_find(x, ".//sca:ClientErrorJobIdNotFound")
    return x is None


def wsd_get_job_elements(hosted_scan_service: wsd_transfer__structures.HostedService,
                         job: wsd_scan__structures.ScanJob):
    """
    Submit a GetJob request, and parse the response.
    The device should reply with info's about the specified job, such as its status,
    the ticket submitted for job initiation, the final parameters set effectively used to scan, and a document list.

    :param hosted_scan_service: the wsd scan service to query
    :type hosted_scan_service: wsd_transfer__structures.HostedService
    :param job: the ScanJob instance representing the job to abort
    :type job: wsd_scan_structures.ScanJob
    :return: a tuple of the form (JobStatus, ScanTicket, DocumentParams, doclist),\
    where doclist is a list of document names
    """
    fields = {"FROM": wsd_common.urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "JOB_ID": job.id}
    x = wsd_common.submit_request({hosted_scan_service.ep_ref_addr},
                                  "ws-scan__get_job_elements.xml",
                                  fields)

    q = wsd_common.xml_find(x, ".//sca:JobStatus")
    jstatus = wsd_scan__parsers.parse_job_status(q)

    st = wsd_common.xml_find(x, ".//sca:ScanTicket")
    tkt = wsd_scan__parsers.parse_scan_ticket(st)

    dfp = wsd_common.xml_find(x, ".//sca:Documents/sca:DocumentFinalParameters")
    dps = wsd_scan__parsers.parse_document_params(dfp)
    dlist = [x.text for x in wsd_common.xml_findall(dfp, "sca:Document/sca:DocumentDescription/sca:DocumentName")]

    return jstatus, tkt, dps, dlist


def wsd_get_active_jobs(hosted_scan_service: wsd_transfer__structures.HostedService) \
        -> typing.List[wsd_scan__structures.JobSummary]:
    """
    Submit a GetActiveJobs request, and parse the response.
    The device should reply with a list of all active scan jobs.

    :param hosted_scan_service: the wsd scan service to query
    :type hosted_scan_service: wsd_transfer__structures.HostedService
    :return: a list of JobSummary elements
    :rtype: list[wsd_scan__structures.JobSummary]
    """
    fields = {"FROM": wsd_common.urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = wsd_common.submit_request({hosted_scan_service.ep_ref_addr},
                                  "ws-scan__get_active_jobs.xml",
                                  fields)

    jsl = []
    for y in wsd_common.xml_findall(x, ".//sca:JobSummary"):
        jsl.append(wsd_scan__parsers.parse_job_summary(y))

    return jsl


def wsd_get_job_history(hosted_scan_service: wsd_transfer__structures.HostedService) \
        -> typing.List[wsd_scan__structures.JobSummary]:
    """
    Submit a GetJobHistory request, and parse the response.
    The device should reply with a list of recently ended jobs.
    Note that some device implementations do not keep or share job history through WSD.

    :param hosted_scan_service: the wsd scan service to query
    :type hosted_scan_service: wsd_transfer__structures.HostedService
    :return: a list of JobSummary elements.
    """
    fields = {"FROM": wsd_common.urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = wsd_common.submit_request({hosted_scan_service.ep_ref_addr},
                                  "ws-scan__get_job_history.xml",
                                  fields)

    jsl = []
    for y in wsd_common.xml_findall(x, ".//sca:JobSummary"):
        jsl.append(wsd_scan__parsers.parse_job_summary(y))

    return jsl


def wsd_retrieve_image(hosted_scan_service: wsd_transfer__structures.HostedService,
                       job: wsd_scan__structures.ScanJob,
                       docname: str) \
        -> typing.Tuple[int, typing.List[Image.Image]]:
    """
    Submit a RetrieveImage request, and parse the response.
    Retrieves a single image from the scanner, if the job has available images to send. If the file format
    selected in the scan ticket was multipage, retrieves a batch of images instead.
    Usually the client has approx. 60 seconds to start images acquisition after the creation of a job.

    :param hosted_scan_service: the wsd scan service to query
    :type hosted_scan_service: wsd_transfer__structures.HostedService
    :param job: the ScanJob instance representing the queried job.
    :type job: wsd_scan__structures.ScanJob
    :param docname: the name assigned to the image to retrieve.
    :type docname: str
    :return: the number of images retrieved, and an array of images
    :rtype: (int, list[PIL.Image])
    """

    data = wsd_common.message_from_file(wsd_common.abs_path("../templates/ws-scan__retrieve_image.xml"),
                                        FROM=wsd_common.urn,
                                        TO=hosted_scan_service.ep_ref_addr,
                                        JOB_ID=job.id,
                                        JOB_TOKEN=job.token,
                                        DOC_DESCR=docname)

    if wsd_common.debug:
        r = etree.fromstring(data.encode("ASCII"), parser=wsd_common.parser)
        print('##\n## RETRIEVE IMAGE REQUEST\n##\n')
        print(etree.tostring(r, pretty_print=True, xml_declaration=True).decode("ASCII"))

    r = requests.post(hosted_scan_service.ep_ref_addr, headers=wsd_common.headers, data=data)

    try:
        x = etree.fromstring(r.text)
        q = wsd_common.xml_find(x, ".//soap:Fault")
        if q is not None:
            e = wsd_common.xml_find(q, ".//soap:Code/soap:Subcode/soap:Value").text
            if e == "wscn:ClientErrorNoImagesAvailable":
                return 0, []
    except etree.ParseError:
        content_with_header = b'Content-type: ' + r.headers['Content-Type'].encode('ascii') + r.content
        m = email.message_from_bytes(content_with_header)

        ls = list(m.walk())

        if wsd_common.debug:
            print('##\n## RETRIEVE IMAGE RESPONSE\n##\n%s\n' % ls[1])

        img = Image.open(BytesIO(ls[2].get_payload(decode=True)))
        print("%s %s %s" % (img.format, img.size, img.mode))

        count = 0
        imglist = []

        for page in ImageSequence.Iterator(img):
            count += 1
            a = Image.new(page.mode, page.size)
            a.putdata(page.getdata())
            imglist.append(a)

        return count, imglist


def __demo():
    wsd_common.init()
    wsd_common.debug = False
    tsl = wsd_discovery__operations.get_devices()
    for a in tsl:
        (ti, hss) = wsd_transfer__operations.wsd_get(a)
        for b in hss:
            if "wscn:ScannerServiceType" in b.types:
                (d, c, s, std_ticket) = wsd_get_scanner_elements(b)
                print(a)
                print(ti)
                print(b)
                print(d)
                print(c)
                print(s)
                print(std_ticket)
                # t.doc_params.input_src = "ADF"
                # t.doc_params.images_num = 0
                (valid, ticket) = wsd_validate_scan_ticket(b, std_ticket)
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
                    while o < ticket.doc_params.images_num:
                        imgnum, imglist = wsd_retrieve_image(b, j, "prova.bmp")
                        for i in imglist:
                            i.save("prova_%d.bmp" % o, "BMP")
                            o += 1


if __name__ == "__main__":
    __demo()
