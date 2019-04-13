import argparse
from urllib.parse import urlparse

from PyWSD import wsd_common, wsd_discovery__operations, wsd_transfer__operations


def noop(args):
    pass


def update_db(args):
    wsd_discovery__operations.set_discovery_verbosity(args.verbosity_lvl)
    wsd_discovery__operations.get_devices(probe_timeout=args.timeout)


def monitor(args):
    wsd_discovery__operations.set_discovery_verbosity(args.verbosity_lvl)
    wsd_discovery__operations.get_devices(probe_timeout=args.timeout)

    db = wsd_discovery__operations.open_db()
    try:
        while True:
            (hello, target) = wsd_discovery__operations.listen_multicast_announcements()
            if hello:
                target = wsd_discovery__operations.wsd_resolve(target)
                wsd_discovery__operations.add_target_to_db(db, target)
            else:
                wsd_discovery__operations.remove_target_from_db(db, target)
    except KeyboardInterrupt:
        pass

    db.close()


def show_list(args):
    db = wsd_discovery__operations.open_db()
    targets = wsd_discovery__operations.read_targets_from_db(db)
    device_types = set()
    if "p" in args.filter:
        device_types.add("wprt:PrintDeviceType")
    if "s" in args.filter:
        device_types.add("wscn:ScanDeviceType")

    print("\n WSD devices:")
    for target in targets:
        if not target.types.isdisjoint(device_types):
            try:
                (info, services) = wsd_transfer__operations.wsd_get(target)
                target_types = set()
                if "wprt:PrintDeviceType" in target.types:
                    target_types.add("Printer")
                if "wscn:ScanDeviceType" in target.types:
                    target_types.add("Scanner")
                dev_id = (info.manufacturer + "_" + info.model_name).replace(" ", "_").replace(".", "")
                dev_classes = "|".join(target_types)
                dev_addr = urlparse(next(iter(target.xaddrs))).netloc
                print(wsd_common.indent(dev_id + " @ " + dev_addr + " [" + dev_classes + "]"))
            except TimeoutError:
                pass
    db.close()


def parse_cmd_line():
    help_filter = "Filter target types: p=printer, s=scanner" \
                  ""
    parser = argparse.ArgumentParser(description='WSD Utility')
    parser.add_argument('-d', '--debug', action="store_true", default=False, required=False, help='Enable debug')
    parser.add_argument('-t', '--timeout', action="store", required=False, type=int, default=2, help='Timeout')
    parser.set_defaults(func=noop)
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument('-f', '--filter', action="store", required=False, type=str, default="ps", help=help_filter)
    list_parser.set_defaults(func=show_list)

    monitor_parser = subparsers.add_parser("monitor")
    monitor_parser.add_argument('-v', '--verbosity_lvl', action="store", type=int, default=0, required=False,
                                help='Enable verbosity')
    monitor_parser.set_defaults(func=monitor)

    update_db_parser = subparsers.add_parser("update_db")
    update_db_parser.add_argument('-v', '--verbosity_lvl', action="store", type=int, default=0, required=False,
                                  help='Enable verbosity')
    update_db_parser.set_defaults(func=update_db)

    args = parser.parse_args()
    args.func(args)


def __main():
    wsd_common.init()
    parse_cmd_line()


if __name__ == "__main__":
    __main()
