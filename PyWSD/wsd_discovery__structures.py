#!/usr/bin/env python3
# -*- encoding: utf-8 -*-


class TargetService:
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
