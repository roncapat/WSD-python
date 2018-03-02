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
                  "FILTER_DIALECT": "http://schemas.xmlsoap.org/ws/2006/02/devprof/Action",
                  "EVENT": event_uri}
    x = submit_request(hosted_service.ep_ref_addr,
                       "ws-eventing__subscribe.xml",
                       fields_map)

    if check_fault(x):
        return False

    return x


def wsd_unsubscribe(hosted_service, subscription_id):
    """
    Unsubscribe from events notifications of a wsd service

    :param hosted_service: the wsd service from which you want to unsubscribe for events
    :param subscription_id: the ID returned from a previous successful event subscription call
    :return: the reply of the wsd service, or False if a fault message is received instead
    """
    fields_map = {"FROM": urn,
                  "TO": hosted_service.ep_ref_addr,
                  "SUBSCRIPTION_ID": subscription_id}
    x = submit_request(hosted_service.ep_ref_addr,
                       "ws-eventing__unsubscribe.xml",
                       fields_map)

    if check_fault(x):
        return False

    return x


def wsd_renew(hosted_service, subscription_id, expiration):
    """
    """
    fields_map = {"FROM": urn,
                  "TO": hosted_service.ep_ref_addr,
                  "SUBSCRIPTION_ID": subscription_id,
                  "EXPIRES": expiration}
    x = submit_request(hosted_service.ep_ref_addr,
                       "ws-eventing__renew.xml",
                       fields_map)

    if check_fault(x):
        return False

    return x


def wsd_get_status(hosted_service, subscription_id):
    """
    """
    fields_map = {"FROM": urn,
                  "TO": hosted_service.ep_ref_addr,
                  "SUBSCRIPTION_ID": subscription_id}
    x = submit_request(hosted_service.ep_ref_addr,
                       "ws-eventing__get_status.xml",
                       fields_map)

    if check_fault(x):
        return False

    return x


if __name__ == "__main__":
    import wsd_scan_events, wsd_transfer, wsd_discovery

    urn = gen_urn()
    tsl = wsd_discovery.get_devices()
    for a in tsl:
        (ti, hss) = wsd_transfer.wsd_get(a)
        for b in hss:
            if "wscn:ScannerServiceType" in b.types:
                listen_addr = "http://192.168.1.109:6666/wsd"
                h = wsd_scan_events.wsd_scanner_all_events_subscribe(b, "P0Y0M0DT30H0M0S", listen_addr)
                wsd_renew(b, h, "2019-06-26T21:07:00.000-08:00")
                wsd_get_status(b, h)
                wsd_unsubscribe(b, h)
