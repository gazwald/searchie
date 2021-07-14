#!/usr/bin/env python3
import ipaddress
import urllib.robotparser
from datetime import datetime
from typing import Dict
from multiprocessing import Pool, cpu_count
import requests
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

index: str = "ipv4addresses"
headers: Dict = {"user-agent": "searchie/0.0.1"}


def get_robots_txt(base_url: str) -> Dict:
    """
    https://docs.python.org/3/library/urllib.robotparser.html
    """
    robots_url = "/".join([base_url, "robots.txt"])
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    rrate = rp.request_rate("*")
    return {
        "requests": rrate.requests,
        "seconds": rrate.seconds,
        "crawl_delay": rp.crawl_delay("*"),
    }


def make_request(
    address: str,
    scheme: str = "http",
    timeout: int = 3,
) -> Dict:
    result = {
        f"{scheme}_available": False,
        f"{scheme}_status_code": -1,
        f"{scheme}_content": "",
        "headers": {},
        "robots": {},
        "last_checked": datetime.now(),
    }
    url = f"{scheme}://{address}"
    r = requests.get(url, headers=headers, timeout=timeout)
    result["{scheme]_status_code"] = r.status_code
    if r.ok:
        result[f"{scheme}_available"] = True
        result["{scheme}_content"] = r.text
        result["headers"] = r.headers
        result["robots"] = get_robots_txt(f"{scheme}://{address}")
        result["last_online"] = datetime.now()

    return result


def get_address(
    address: ipaddress.IPv4Address,
    http: bool = True,
    https: bool = True,
) -> Dict:

    result = dict()
    result_http = dict()
    result_https = dict()

    if http:
        result_http = make_request(address, "http")

    if https:
        result_https = make_request(address, "https")

    result = {**result_http, **result_https}
    result["last_checked"] = datetime.now()

    return result


def process_entry(item: Dict) -> None:
    http = item["_source"]["http_available"]
    https = item["_source"]["https_available"]
    address = ipaddress.IPv4Address(item["_source"]["address"])
    result = get_address(address, http, https)
    es.update(index, id=item["id"], body=result)


def main():
    query = {"query": {"match_all": {}}}

    with Pool(cpu_count() * 2) as p:
        p.map(process_entry, scan(es, index=index, query=query))


if __name__ == "__main__":
    es = Elasticsearch()
    main()
