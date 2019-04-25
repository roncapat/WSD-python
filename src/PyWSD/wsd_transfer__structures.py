#!/usr/bin/env python3
# -*- encoding: utf-8 -*-


class TargetInfo:
    """
    Holds information about a certain target service, such as name, model, manufacturer, and so on.
    """

    def __init__(self):
        self.manufacturer = ""
        self.manufacturer_url = ""
        self.model_name = ""
        self.model_number = ""
        self.model_url = ""
        self.presentation_url = ""
        self.device_cat = []
        self.friendly_name = ""
        self.fw_ver = ""
        self.serial_num = ""

    def __str__(self):
        s = ""
        s += "Friendly name:        %s\n" % self.friendly_name
        s += "Model name:           %s\n" % self.model_name
        s += "Model number:         %s\n" % self.model_number
        s += "Device categories:    %s\n" % ', '.join(self.device_cat)
        s += "Manufacturer:         %s\n" % self.manufacturer

        s += "Firmware version:     %s\n" % self.fw_ver
        s += "Serial number:        %s\n" % self.serial_num

        s += "Manufacturer URL:     %s\n" % self.manufacturer_url
        s += "Model URL:            %s\n" % self.model_url
        s += "Web UI URL:           %s\n" % self.presentation_url
        return s


class HostedService:
    """
    An actual service offered by a certain wsd target. Each device is a target, but
    a target can publish multiple hosted services at once.
    """

    def __init__(self):
        self.types = []
        self.service_id = ""
        self.hardware_id = ""
        self.compatible_id = ""
        self.service_address = ""
        self.ep_ref_addr = ""

    def __str__(self):
        s = ""
        s += "Service path:         %s\n" % self.ep_ref_addr
        s += "Service ID:           %s\n" % self.service_id
        s += "Service types:        %s\n" % ', '.join(self.types)
        s += "Compatible IDs:       %s\n" % self.compatible_id
        s += "Hardware ID:          %s\n" % self.hardware_id
        s += "Service address:      %s\n" % self.service_address
        return s
