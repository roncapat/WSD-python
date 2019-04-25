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
        self.relates_to = None  # allowed only if a proxy replies to a multicast probe
        self.app_sequence = [0, 0, 0]  # instance, sequence, message IDs
        self.ts = TargetService()

    def is_valid(self):
        valid = True
        valid = valid & (self.message_id is not None)
        valid = valid & (self.ts.ep_ref_addr is not None)
        return valid

    def get_target_service(self):
        if not self.is_valid():
            print("Warning: invalid TargetService")
        return self.ts


class ByeMessage:
    def __init__(self):
        self.action = "http://schemas.xmlsoap.org/ws/2005/04/discovery/Bye"
        self.message_id = None
        self.app_sequence = [0, 0, 0]  # instance, sequence, message IDs
        self.ts = TargetService()

    def is_valid(self):
        valid = True
        valid = valid & (self.message_id is not None)
        valid = valid & (self.ts.ep_ref_addr is not None)
        return valid

    def get_target_service(self):
        if not self.is_valid():
            print("Warning: invalid TargetService")
        return self.ts


class ProbeMatchesMessage:
    def __init__(self):
        self.action = "http://schemas.xmlsoap.org/ws/2005/04/discovery/ProbeMatches"
        self.message_id = None
        self.relates_to = None
        self.to = None
        self.app_sequence = [0, 0, 0]  # instance, sequence, message IDs
        self.matches = []  # at most one element if not from a discovery proxy

    def is_valid(self):
        valid = True
        valid = valid & (self.message_id is not None)
        valid = valid & (self.relates_to is not None)
        valid = valid & (self.to is not None)
        for ts in self.matches:
            valid = valid & (ts.ep_ref_addr is not None)
        return valid

    def get_target_services(self):
        if not self.is_valid():
            print("Warning: invalid TargetService")
        return self.matches


class ResolveMatchesMessage:
    def __init__(self):
        self.action = "http://schemas.xmlsoap.org/ws/2005/04/discovery/ResolveMatches"
        self.message_id = None
        self.relates_to = None
        self.to = None
        self.app_sequence = [0, 0, 0]  # instance, sequence, message IDs
        self.ts = None  # Allowed None only if it's a response from a discovery proxy

    def is_valid(self):
        valid = True
        valid = valid & (self.message_id is not None)
        valid = valid & (self.relates_to is not None)
        valid = valid & (self.to is not None)
        if self.ts is not None:
            valid = valid & (self.ts.ep_ref_addr is not None)
            valid = valid & (len(self.ts.xaddrs) > 0)
        return valid

    def get_target_service(self):
        if not self.is_valid():
            print("Warning: invalid TargetService")
        return self.ts
