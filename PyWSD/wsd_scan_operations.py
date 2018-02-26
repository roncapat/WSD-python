#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import email

import wsd_discovery
import wsd_transfer
from wsd_scan_parsers import *


def wsd_get_scanner_elements(hosted_scan_service):
    """
    Submit a GetScannerElements request, and parse the response.
    The device should reply with informations about itself,
    its configuration, its status and the defalt scan ticket

    :param hosted_scan_service: the wsd scan service to query
    :return: a tuple of the form (ScannerDescription, ScannerConfiguration, ScannerStatus, ScanTicket)
    """
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_getscannerelements.xml",
                       fields,
                       "GET SCANNER ELEMENTS")

    re = xml_find(x, ".//sca:ScannerElements")
    sca_status = xml_find(re, ".//sca:ScannerStatus")
    sca_config = xml_find(re, ".//sca:ScannerConfiguration")
    sca_descr = xml_find(re, ".//sca:ScannerDescription")
    std_ticket = xml_find(re, ".//sca:DefaultScanTicket")

    description = parse_scan_description(sca_descr)
    status = parse_scan_status(sca_status)
    config = parse_scan_configuration(sca_config)
    std_ticket = parse_scan_ticket(std_ticket)

    return description, config, status, std_ticket


def wsd_validate_scan_ticket(hosted_scan_service, tkt):
    """
    Submit a ValidateScanTicket request, and parse the response.
    Scanner devices can validate scan settings/parameters and fix errors if any. It is recommended to always
    validate a ticket before submitting the actual scan job.

    :param hosted_scan_service: the wsd scan service to query
    :param tkt: the ScanTicket to submit for validation purposes
    :return: a tuple of the form (boolean, ScanTicket), where the first field is True if no errors were found during\
    validation, along with the same ticket submitted, or False if errors were found, along with a corrected ticket.
    """

    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_validatescanticket.xml",
                       {**fields, **tkt.as_map()},
                       "VALIDATE SCAN TICKET")

    v = xml_find(x, ".//sca:ValidTicket")
    is_valid = True if v.text == 'true' or v.text == '1' else False
    if is_valid:
        return True, tkt
    else:
        return False, parse_scan_ticket(xml_find(x, ".//sca::ValidScanTicket"))


def wsd_create_scan_job(hosted_scan_service, tkt, scan_identifier="", dest_token=""):
    """
    Submit a CreateScanJob request, and parse the response.
    This creates a scan job and starts the image(s) acquisition.

    :param hosted_scan_service: the wsd scan service to query
    :param tkt: the ScanTicket to submit for validation purposes
    :param scan_identifier: a string identifying the device-initiated scan to handle, if any
    :param dest_token: a token assigned by the scanner to this client, needed for device-initiated scans
    :return: a ScanJob instance
    """

    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "SCAN_ID": scan_identifier,
              "DEST_TOKEN": dest_token}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_createscanjob.xml",
                       {**fields, **tkt.as_map()},
                       "CREATE SCAN JOB")

    scnj = ScanJob()
    x = xml_find(x, ".//sca:CreateScanJobResponse")
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


def wsd_retrieve_image(hosted_scan_service, job, docname):
    """
    Submit a RetrieveImage request, and parse the response.
    Retrieves a single image from the scanner, if the job has available images to send.
    Usually the client has approx. 60 seconds to start images acquisition after the creation of a job.
    For multiple sheets scans, user should submit this request in a loop until False is returned.

    :param hosted_scan_service: the wsd scan service to query
    :param job: the ScanJob instance representing the queried job.
    :param docname: the name assigned to the image to retrieve.
    :return: True if image is available, False otherwise
    """

    data = message_from_file(abs_path("../templates/ws-scan_retrieveimage.xml"),
                             FROM=urn,
                             TO=hosted_scan_service.ep_ref_addr,
                             JOB_ID=job.id,
                             JOB_TOKEN=job.token,
                             DOC_DESCR=docname)

    if debug:
        r = etree.fromstring(data.encode("ASCII"), parser=parser)
        print('##\n## RETRIEVE IMAGE REQUEST\n##\n')
        print(etree.tostring(r, pretty_print=True, xml_declaration=True).decode("ASCII"))

    r = requests.post(hosted_scan_service.ep_ref_addr, headers=headers, data=data)

    try:
        x = etree.fromstring(r.text)
        q = xml_find(x, ".//soap:Fault")
        if q is not None:
            e = xml_find(q, ".//soap:Code/soap:Subcode/soap:Value").text
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
    """
    Submit a CancelJob request, and parse the response.
    Stops and aborts the specified scan job.

    :param hosted_scan_service: the wsd scan service to query
    :param job: the ScanJob instance representing the job to abort
    :return: True if the job is found and then aborted, False if the specified job do not exists or already ended.
    """
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "JOB_ID": job.id}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_canceljob.xml",
                       fields,
                       "CANCEL JOB")

    xml_find(x, ".//sca:ClientErrorJobIdNotFound")
    return x is None


def wsd_get_job_elements(hosted_scan_service, job):
    """
    Submit a GetJob request, and parse the response.
    The device should reply with info's about the specified job, such as its status,
    the ticket submitted for job initiation, the final parameters set effectively used to scan, and a document list.

    :param hosted_scan_service: the wsd scan service to query
    :param job: the ScanJob instance representing the job to abort
    :return: a tuple of the form (JobStatus, ScanTicket, DocumentParams, doclist),\
    where doclist is a list of document names
    """
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr,
              "JOB_ID": job.id}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_getjobelements.xml",
                       fields,
                       "GET JOB ELEMENTS")

    q = xml_find(x, ".//sca:JobStatus")
    jstatus = parse_job_status(q)

    st = xml_find(x, ".//sca:ScanTicket")
    tkt = parse_scan_ticket(st)

    ds = xml_find(x, ".//sca:Documents")
    dfp = xml_find(ds, "sca:DocumentFinalParameters")
    dps = parse_document_params(dfp)
    dlist = [x.text for x in xml_findall(dfp, "sca:Document/sca:DocumentDescription/sca:DocumentName")]

    return jstatus, tkt, dps, dlist


def wsd_get_active_jobs(hosted_scan_service):
    """
    Submit a GetActiveJobs request, and parse the response.
    The device should reply with a list of all active scan jobs.

    :param hosted_scan_service: the wsd scan service to query
    :return: a list of JobStatus elements
    """
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_getactivejobs.xml",
                       fields,
                       "GET ACTIVE JOBS")

    jsl = []
    for y in xml_findall(x, ".//sca:JobSummary"):
        jsum = JobSummary()
        jsum.name = xml_find(y, "sca:JobName").text
        jsum.user_name = xml_find(y, "sca:JobOriginatingUserName").text
        jsum.status = parse_job_status(y)
        jsl.append(jsum)

    return jsl


def wsd_get_job_history(hosted_scan_service):
    """
    Submit a GetJobHistory request, and parse the response.
    The device should reply with a list of recently ended jobs.
    Note that some device implementations do not keep or share job history through WSD.

    :param hosted_scan_service: the wsd scan service to query
    :return: a list of JobStatus elements.
    """
    fields = {"FROM": urn,
              "TO": hosted_scan_service.ep_ref_addr}
    x = submit_request(hosted_scan_service.ep_ref_addr,
                       "ws-scan_getjobhistory.xml",
                       fields,
                       "GET JOB HISTORY")

    jsl = []
    for y in xml_findall(x, ".//sca:JobSummary"):
        jsum = JobSummary()
        jsum.name = xml_find(y, "sca:JobName").text
        jsum.user_name = xml_find(y, "sca:JobOriginatingUserName").text
        jsum.status = parse_job_status(y)
        jsl.append(jsum)

    return jsl


def __demo():
    (debug, timeout) = parse_cmd_line()
    urn = gen_urn()
    tsl = wsd_discovery.get_devices()
    for a in tsl:
        (ti, hss) = wsd_transfer.wsd_get(a)
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
                    while wsd_retrieve_image(b, j, "test_%d.jpeg" % o):
                        o = o + 1


if __name__ == "__main__":
    __demo()
