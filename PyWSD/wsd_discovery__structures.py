#!/usr/bin/env python3
# -*- encoding: utf-8 -*-


class TargetService:
    """
    A WSD target service is an abstract entity that can be discovered on the network.
    Each WSD device must not impersonate more than one target service, even if it
    hosts multiple services like printing, scanning, etc.
    """
    def __init__(self):
        self.ep_ref_addr = ""
        self.types = set()
        self.scopes = set()
        self.xaddrs = set()
        self.meta_ver = 0

    def __str__(self):
        s = ""
        s += "EndPoint reference:   %s\n" % self.ep_ref_addr
        s += "Metadata version:     %d\n" % self.meta_ver
        s += "Implemented Types:    %s\n" % ', '.join(self.types)
        s += "Assigned Scopes:      %s\n" % ', '.join(self.scopes)
        s += "Transport addresses:  %s\n" % ', '.join(self.xaddrs)
        return s

    def __eq__(self, other):
        return self.ep_ref_addr == other.ep_ref_addr

    def __hash__(self):
        return self.ep_ref_addr.__hash__()


class HelloMessage:
    def __init__(self):
        self.action = "http://schemas.xmlsoap.org/ws/2005/04/discovery/Hello"
        self.message_id = None
        self.relates_to = None         # allowed only if a proxy replies to a multicast probe
        self.app_sequence = [0, 0, 0]  # instance, sequence, message IDs
        self.ep_ref_addr = None
        self.types = set()
        self.scopes = set()
        self.xaddrs = set()
        self.metadata_version = None

    def is_valid(self):
        valid = True
        valid = valid & (self.message_id is not None)
        valid = valid & (self.ep_reference is not None)
        valid = valid & (self.metadata_version is not None)
        return valid

    def get_target_service(self):
        ts = TargetService()
        ts.ep_ref_addr = self.ep_ref_addr
        ts.types = self.types
        ts.scopes = self.scopes
        ts.xaddrs = self.xaddrs
        ts.meta_ver = self.metadata_version
        return ts


class ByeMessage:
    def __init__(self):
        self.action = "http://schemas.xmlsoap.org/ws/2005/04/discovery/Bye"
        self.message_id = None
        self.app_sequence = [0, 0, 0]  # instance, sequence, message IDs
        self.ep_ref_addr = None

    def is_valid(self):
        valid = True
        valid = valid & (self.message_id is not None)
        valid = valid & (self.ep_reference is not None)
        return valid

    def get_target_service(self):
        ts = TargetService()
        ts.ep_ref_addr = self.ep_ref_addr
        return ts

