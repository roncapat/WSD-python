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
    '''
    Submit a GetScannerElements request, and parse the response.
    The device should reply with informations about itself,
    its configuration, its status and the defalt scan ticket

    :param hosted_scan_service: the wsd scan service to query
    :return: a tuple of the form (ScannerDescription, ScannerConfiguration, ScannerStatus, ScanTicket)
    '''
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

    description = parse_scan_description(sca_descr)
    status = parse_scan_status(sca_status)
    config = parse_scan_configuration(sca_config)
    std_ticket = parse_scan_ticket(std_ticket)

    return description, config, status, std_ticket


def wsd_validate_scan_ticket(hosted_scan_service, tkt):
    '''
    Submit a ValidateScanTicket request, and parse the response.
    Scanner devices can validate scan settings/parameters and fix errors if any. It is recommended to always
    validate a ticket before submitting the actual scan job.

    :param hosted_scan_service: the wsd scan service to query
    :param tkt: the ScanTicket to submit for validation purposes
    :return: a tuple of the form (boolean, ScanTicket), where the first field is True if no errors were found during\
    validation, along with the same ticket submitted, or False if errors were found, along with a corrected ticket.
    '''

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
    '''
    Submit a CreateScanJob request, and parse the response.
    This creates a scan job and starts the image(s) acquisition.

    :param hosted_scan_service: the wsd scan service to query
    :param tkt: the ScanTicket to submit for validation purposes
    :param scan_identifier: a string identifying the device-initiated scan to handle, if any
    :param dest_token: a token assigned by the scanner to this client, needed for device-initiated scans
    :return: a ScanJob instance
    '''

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
    '''
    Submit a RetrieveImage request, and parse the response.
    Retrieves a single image from the scanner, if the job has available images to send.
    Usually the client has approx. 60 seconds to start images acquisition after the creation of a job.
    For multiple sheets scans, user should submit this request in a loop until False is returned.

    :param hosted_scan_service: the wsd scan service to query
    :param job: the ScanJob instance representing the queried job.
    :return: True if image is available, False otherwise
    '''

    data = message_from_file(abs_path("../templates/ws-scan_retrieveimage.xml"),
                             FROM=urn,
                             TO=hosted_scan_service.ep_ref_addr,
                             JOB_ID=job.id,
                             JOB_TOKEN=job.token,
                             DOC_DESCR=docname)

    if debug:
        r = etree.fromstring(data, parser=parser)
        print('##\n## RETRIEVE IMAGE REQUEST\n##\n')
        print(etree.tostring(r, pretty_print=True, xml_declaration=True))

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

    x.find(".//sca:ClientErrorJobIdNotFound", NSMAP)
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
    for y in x.findall(".//sca:JobSummary", NSMAP):
        jsum = JobSummary()
        jsum.name = y.find("sca:JobName", NSMAP).text
        jsum.user_name = y.find("sca:JobOriginatingUserName", NSMAP).text
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
