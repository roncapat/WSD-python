import typing
from lxml import etree
import wsd_common
import wsd_discovery__structures


def get_sequence(xml_tree: etree.ElementTree) -> typing.List[int]:
    q = wsd_common.xml_find(xml_tree, ".//wsd:AppSequence")
    seq = [0, 0, 0]
    seq[0] = int(q.attrib['InstanceId'])
    if 'SequenceId' in q.attrib:
        seq[1] = int(q.attrib['SequenceId'])
    seq[2] = int(q.attrib['MessageNumber'])
    return seq


def parser_target(xml_tree: etree.ElementTree) -> wsd_discovery__structures.TargetService:
    o = wsd_discovery__structures.TargetService()
    o.ep_ref_addr = wsd_common.get_xml_str(xml_tree, ".//wsa:EndpointReference/wsa:Address")
    o.types = wsd_common.get_xml_str_set(xml_tree, ".//wsd:Types")
    o.scopes = wsd_common.get_xml_str_set(xml_tree, ".//wsd:Scopes")
    o.xaddrs = wsd_common.get_xml_str_set(xml_tree, ".//wsd:XAddrs")
    o.metadata_version = wsd_common.get_xml_int(xml_tree, ".//wsd:MetadataVersion")
    return o


def parser_hello(xml_tree: etree.ElementTree) -> wsd_discovery__structures.HelloMessage:
    o = wsd_discovery__structures.HelloMessage()
    header = wsd_common.get_header_tree(xml_tree)
    o.message_id = wsd_common.get_xml_str(header, ".//wsa:MessageID")
    o.relates_to = wsd_common.get_xml_str(header, ".//wsa:RelatesTo")
    o.app_sequence = get_sequence(header)
    body = wsd_common.get_body_tree(xml_tree)
    o.ts = parser_target(body)
    return o


def parser_bye(xml_tree: etree.ElementTree) -> wsd_discovery__structures.ByeMessage:
    o = wsd_discovery__structures.ByeMessage()
    header = wsd_common.get_header_tree(xml_tree)
    o.message_id = wsd_common.get_xml_str(header, ".//wsa:MessageID")
    o.app_sequence = get_sequence(header)
    body = wsd_common.get_body_tree(xml_tree)
    o.ts = parser_target(body)
    return o


def parser_probe_match(xml_tree: etree.ElementTree) -> wsd_discovery__structures.ProbeMatchesMessage:
    o = wsd_discovery__structures.ProbeMatchesMessage()
    header = wsd_common.get_header_tree(xml_tree)
    o.message_id = wsd_common.get_xml_str(header, ".//wsa:MessageID")
    o.relates_to = wsd_common.get_xml_str(header, ".//wsa:RelatesTo")
    o.to = wsd_common.get_xml_str(header, ".//wsa:To")
    o.app_sequence = get_sequence(header)
    body = wsd_common.get_body_tree(xml_tree)
    matches = wsd_common.xml_findall(body, "wsd:ProbeMatches/wsd:ProbeMatch")
    for match in matches:
        o.matches.append(parser_target(match))
    return o


def parser_resolve_match(xml_tree: etree.ElementTree) -> wsd_discovery__structures.ResolveMatchesMessage:
    o = wsd_discovery__structures.ResolveMatchesMessage()
    header = wsd_common.get_header_tree(xml_tree)
    o.message_id = wsd_common.get_xml_str(header, ".//wsa:MessageID")
    o.relates_to = wsd_common.get_xml_str(header, ".//wsa:RelatesTo")
    o.to = wsd_common.get_xml_str(header, ".//wsa:To")
    o.app_sequence = get_sequence(header)
    body = wsd_common.get_body_tree(xml_tree)
    match = wsd_common.xml_findall(body, "wsd:ResolveMatches/wsd:ResolveMatch")
    if match is not None:
        o.ts = parser_target(body)
    return o


def init()->None:
    wsd_common.register_message_parser("http://schemas.xmlsoap.org/ws/2005/04/discovery/Hello", parser_hello)
    wsd_common.register_message_parser("http://schemas.xmlsoap.org/ws/2005/04/discovery/Bye", parser_bye)
    wsd_common.register_message_parser("http://schemas.xmlsoap.org/ws/2005/04/discovery/ProbeMatches", parser_probe_match)
    wsd_common.register_message_parser("http://schemas.xmlsoap.org/ws/2005/04/discovery/ResolveMatches", parser_resolve_match)

init()
