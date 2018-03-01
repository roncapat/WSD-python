#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from wsd_common import *


def wsd_subscribe(hosted_service, event_uri, expiration, notify_addr):
    """
    Subscribe to a certain type of events of a wsd service

    :param hosted_service: the wsd service to receive event notifications from
    :param event_uri: the full URI of the targeted event class. \
                    Those URIs are taken from ws specifications
    :param expiration: Expiration time, as a string in the following form: P*Y**M**DT**H**M**S
    :param notify_addr: The address to send notifications to.
    :return: the reply of the wsd service, or False if a fault message is received instead
    """
    fields_map = {"FROM": urn,
                  "TO": hosted_service.ep_ref_addr,
                  "NOTIFY_ADDR": notify_addr,
                  "EXPIRES": expiration,
                  "EVENT": event_uri}
    x = submit_request(hosted_service.ep_ref_addr,
                       "ws-scan__event_subscribe.xml",
                       fields_map)

    if check_fault(x):
        return False

    return x

# TODO: implement getStatus, Unsubscribe, Renew
