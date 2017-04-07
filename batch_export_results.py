#!/usr/bin/env python
# coding=utf-8
""" Code sample demonstrating exporting results with the Intelligent Voice API
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import json
import requests

path_to_export_to = "/tmp/export12"
group_to_export = 12

iv_server_fqdn = "iv.example.com"
self_signed_cert_path = "C:\\ssl\\ca-cert.pem"  # set to None if using real SSL cert

api_key = "api-user"
api_pass = ""

ws_path = "https://{}:8443/vrxServlet/ws/VRXService/vrxServlet/".format(iv_server_fqdn)


def enum(**enums):
    return type('Enum', (), enums)


export_type = enum(Email=1, Text=2, SmartTranscript=3)
dat_file = enum(No=0, Yes=1)

selection = {
    "ExportSelection": {
        "exportFolder": path_to_export_to,
        "client": group_to_export,
        "exportType": export_type.SmartTranscript,
        "datFile": dat_file.Yes
    }
}

requests.post("{}ExportGroupToFolder".format(ws_path), auth=(api_key, api_pass),
              data=json.dumps(selection), verify=self_signed_cert_path)
