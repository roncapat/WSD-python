I'm a student, and I don't have a job yet, so if you like my repo, please consider 
to gift me a cup of coffee :coffee: 

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](
https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YRKMLJXGDD7XN)


# PyWSD
Web Services for Devices (WSD) tools and utilities for cross platform support.

## Documentation
You can browse the documentation on [readthedocs.io](http://wsd-python.readthedocs.io/en/master/index.html).

## Abstract
The Web Services for Devices is a set of specifications aimed to handle network 
communication between devices which offer some kind of functionality or need to signal events. 
There's a discovery protocol, a way to retrieve a list of services from endpoints, 
and a set of rules built on top of XML/SOAP messages over UDP for commands/events.

Windows uses WSD as a way to discover and interact with a wide range of printers 
and scanners nowadays. Other WSD applications are less-known, but this project 
aims to cover the standard with a generic set of tools suitable even for those devices.

Linux and Mac OS users everyday have to deal with a not-so-good (or absent) full support 
for printers/scanners. For example, Canon does not support Linux at all, and distributes 
bugged drivers that are not fully open source, nor integrates well with existing and 
coherent Linux printing and scanning frameworks. Device-initiated operations are not 
supported at all. This is going to change: WSD standards are not well-known, but fortunately 
they are documented, and easy to reverse-engineer if needed.

So my idea is to get a good comprehension of the protocol, implement a draft library 
and a set of associated tools in python, then test it until the implementation is mature. 
The natural next step will be C implementation, that will finally enable the SANE and CUPS 
wsd backends implementations. 

A library for simulating/implementing new WSD devices could also be developed, and it would 
allow seamless integration of devices shared from a linux instance and a Windows-enabled 
client, for example. 


## Developer notes
Required python version: **3.6**\
Docstring style complies [IntelliJ PyCharm suggestions](
https://www.jetbrains.com/help/pycharm/type-hinting-in-pycharm.html#legacy)

## Project status
As you can see, I'm the only developer. I need people to test my library, develop tools 
from it (some demo bits are among the modules, but they're just for on-the-fly debug 
while developing). 

Here's the list of targets for now:

* Python library for scanners (70% done IMHO)
* C library for scanners
* SANE backend for scanners
* Linux daemon for device-initiated scans


## Protocol public resources (PDF/DOC/HTML from MSDN/W3C/SOAP)
[WS-Discovery](http://specs.xmlsoap.org/ws/2005/04/discovery/ws-discovery.pdf)\
[WS-Transfer](https://www.w3.org/Submission/WS-Transfer)\
[PNP-X](http://download.microsoft.com/download/a/f/7/af7777e5-7dcd-4800-8a0a-b18336565f5b/PnPX-spec.doc)

[WSD-Profiles](http://specs.xmlsoap.org/ws/2006/02/devprof/devicesprofile.pdf)

[WS-Print](http://download.microsoft.com/download/E/9/7/E974CFCB-4B3B-40CC-AF92-4F7F84477F0B/Printer.zip)\
[WS-Scan](http://download.microsoft.com/download/9/C/5/9C5B2167-8017-4BAE-9FDE-D599BAC8184A/ScanService.zip)

