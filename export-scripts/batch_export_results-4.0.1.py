#!/usr/bin/env python
# coding=utf-8
""" Code sample demonstrating exporting results with 4.0.1 Intelligent Voice API
"""
import sys
import json
import logging
import requests
from enum import Enum

iv_server = "iv-staging-1.chaseits.co.uk"

class Export_Type(Enum):
    Email=1
    Text=2
    SmartTranscript=3

class Dat_File(Enum):
    No=0
    Yes=1

# Set exportation parameters
path_to_export_to = "/home/chase/export"
group_to_export = 1
export_type = Export_Type.SmartTranscript
dat_file = Dat_File.No
search_term = ""
search_file = ""

api_key = "tommy"
api_pass = "tomcat"

ws_path = "https://{}:8443/vrxServlet/ws/VRXService/vrxServlet".format(iv_server)

def export_group_to_folder():
    logging.info("Exporting group {} to {}".format(group_to_export, path_to_export_to))

    selection = {
        "ExportSelection": {
            "exportFolder": path_to_export_to,
            "client": group_to_export,
            "exportType": export_type.value,
            "datFile": dat_file.value,
            "searchTerm" : search_term,
            "searchFile" : search_file
        }
    }
    response = requests.post("{}/ExportGroupToFolder".format(ws_path), auth=(api_key, api_pass),
               headers={"Content-Type" : "application/json", "Accept" : "application/json"},
               json=selection, verify=False)
    if (response.status_code == requests.codes.ok):
        logging.info("The group has been exported successfully")
    else:
        raise Exception('could not export group. response was:{}'.format(response.text))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    requests.packages.urllib3.disable_warnings()
    export_group_to_folder()
