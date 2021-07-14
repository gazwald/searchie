#!/usr/bin/env python3
import ipaddress
import logging
import sys
from typing import List
from datetime import datetime
from multiprocessing import Pool, cpu_count

from elasticsearch import Elasticsearch, helpers


class PublicAddresses:
    def __init__(self, subnet: ipaddress.IPv4Network):
        self.subnet = subnet

    @staticmethod
    def subnet_is_global(subnet: ipaddress.IPv4Network) -> bool:
        if (
            not subnet.is_multicast
            and not subnet.is_private
            and not subnet.is_loopback
            and not subnet.is_link_local
        ):
            return True

        return False

    @staticmethod
    def seed(mask: str = "0.0.0.0/0") -> List:
        logging.info("Seeding subnet list...")
        wildcard = ipaddress.ip_network(mask)
        return [
            subnet
            for subnet in wildcard.subnets(new_prefix=24)
            if PublicAddresses.subnet_is_global(subnet)
        ]

    def __iter__(self):
        for address in self.subnet.hosts():
            if address.is_global:
                yield {
                    "_index": "ipv4addresses",
                    "address": str(address),
                    "http_available": True,
                    "http_status_code": -1,
                    "http_content": "",
                    "https_available": True,
                    "https_status_code": -1,
                    "https_content": "",
                    "headers": {},
                    "robots": {},
                    "last_checked": datetime.now(),
                }


def process_addresses(subnet: ipaddress.IPv4Network) -> None:
    logging.debug(f"Processing {subnet}")
    helpers.bulk(es, PublicAddresses(subnet))


def main() -> None:
    subnets = PublicAddresses.seed()
    logging.info(f"Found {len(subnets)} subnets.")
    logging.info("Starting")
    with Pool(cpu_count() + 2) as p:
        p.map(process_addresses, subnets)
    logging.info("Finished")


if __name__ == "__main__":
    log_level = getattr(logging, 'INFO')

    logging.basicConfig(
        stream=sys.stdout,
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    es = Elasticsearch()
    main()
