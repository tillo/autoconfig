"""GET /mail/config-v1.1.xml is the boundary a mail client reads, and it has broken before.

The document is what Thunderbird (and every client that speaks its autoconfig format)
turns into account settings. Its server blocks changed under it twice: 5a85a32 moved IMAP
from STARTTLS to IMAPS, f443eb7 moved SMTP from 25 to the 587 submission port. These
tests drive the real handler over HTTP the way a client does and parse what it gets back.

The domain comes from the request's Host header and the names from the environment, so
neither may reach the XML unescaped: a `&` or `<` there turns the document into one no
client can parse (or, from a forged Host, into one with extra elements in it).
"""
from __future__ import annotations

import http.client
import importlib.util
import os
import socket
import threading
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

_spec = importlib.util.spec_from_file_location(
    "server", Path(__file__).absolute().parent.parent / "server.py")
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)

ENV = {"DISPLAY_NAME": "Example Mail", "DISPLAY_SHORT_NAME": "Example",
       "MAIL_HOSTNAME": "mail.example.org"}


class Autoconfig(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, ENV)
        self.env.start()
        self.quiet = mock.patch.object(server.MyServer, "log_message")
        self.quiet.start()
        self.httpd = server.make_server(("127.0.0.1", 0))
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.quiet.stop()
        self.env.stop()

    def get(self, path, host="autoconfig.example.org"):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=5)
        conn.putrequest("GET", path, skip_host=True)
        if host is not None:
            conn.putheader("Host", host)
        conn.endheaders()
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, resp.getheader("Content-type"), body

    def provider(self, host="autoconfig.example.org"):
        status, ctype, body = self.get(
            "/mail/config-v1.1.xml?emailaddress=user%40example.org", host)
        self.assertEqual((status, ctype), (200, "text/xml"))
        return ET.fromstring(body).find("emailProvider")

    def test_the_client_gets_imaps_993_and_submission_587_on_the_mail_host(self):
        p = self.provider()
        self.assertEqual(p.get("id"), "example.org")
        self.assertEqual(p.findtext("domain"), "example.org")
        self.assertEqual(p.findtext("displayName"), "Example Mail")
        self.assertEqual(p.findtext("displayShortName"), "Example")
        servers = {s.get("type"): {c.tag: c.text for c in s}
                   for s in p if s.tag.endswith("Server")}
        common = {"hostname": "mail.example.org", "username": "%EMAILADDRESS%",
                  "authentication": "password-cleartext"}
        self.assertEqual(servers, {
            "imap": {**common, "port": "993", "socketType": "SSL"},
            "smtp": {**common, "port": "587", "socketType": "STARTTLS"}})

    def test_markup_in_the_host_header_or_the_names_stays_text(self):
        with mock.patch.dict(os.environ, {"DISPLAY_NAME": "Smith & Sons <mail>"}):
            p = self.provider(host='autoconfig.ex"<x/>&.org')
        self.assertEqual(p.get("id"), 'ex"<x/>&.org')
        self.assertEqual(p.findtext("domain"), 'ex"<x/>&.org')
        self.assertIsNone(p.find("domain/x"))
        self.assertEqual(p.findtext("displayName"), "Smith & Sons <mail>")

    def test_a_request_without_a_host_gets_400_not_an_empty_200(self):
        for host in (None, ""):
            with self.subTest(host=host):
                status, ctype, body = self.get(
                    "/mail/config-v1.1.xml?emailaddress=user%40example.org", host)
                self.assertEqual((status, ctype), (400, "text/plain"))
                self.assertIn(b"Host", body)

    def test_a_stalled_client_does_not_block_the_next_one(self):
        # A client that connects and never finishes its request line holds the
        # handler in readline(); one such client must not stall every mail client.
        # Closed inside the test, not in a cleanup: tearDown's shutdown() would
        # otherwise wait on a serving thread that is still stuck on it.
        with socket.create_connection(self.httpd.server_address, timeout=1) as stalled:
            stalled.sendall(b"GET /mail/config-v1.1.xml HTTP/1.1")
            conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=1)
            try:
                conn.request("GET", "/", headers={"Host": "autoconfig.example.org"})
                self.assertEqual(conn.getresponse().status, 200)
            finally:
                conn.close()

    def test_any_other_path_answers_the_plain_text_banner(self):
        status, ctype, body = self.get("/")
        self.assertEqual((status, ctype), (200, "text/plain"))
        self.assertIn(b"Autoconfig server", body)


if __name__ == "__main__":
    unittest.main()
