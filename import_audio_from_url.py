#!/usr/bin/env python
# coding=utf-8
""" Code sample demonstrating importing an audio file using Intelligent Voice API v2 (available from V4.0)
"""
import json
import logging

import requests
from time import sleep, time

import urllib3

iv_api = "https://iv-staging.chaseits.co.uk:8443/vrxServlet/v2"
login = ("tommy", "tomcat")  # see the admin guide or API docs for details on setting up API credentials
cert = '/opt/jumpto/ssl/ca-cert.pem'
iv_group = 2
sample_audio = 'http://http-ws.bbc.co.uk.edgesuite.net/mp3/learningenglish/2014/09/bbc_witn_cyclists_report_140915_witn_cycling_report_au_bb.mp3'


def start_import(audio_files_to_import, group):
    import_selection = {"importFolder": audio_files_to_import, "modelId": 1,
                        "diarizationEnabled": True, "treatAllFilesAsSingleChannel": True}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.post("{}/imports".format(iv_api), auth=login, headers=headers,
                             json=import_selection, verify=cert, params={"userId": "1", "groupId": group})
    return json.loads(response.text)[u'importId']


def get_import_details(import_id):
    response = requests.get('{}/imports/{}'.format(iv_api, import_id), auth=login, verify=cert, params={"userId": 1})
    return json.loads(response.text)


def get_item_details(item_id, group):
    response = requests.get('{}/items/{}'.format(iv_api, item_id), auth=login, verify=cert, params={"userId": "1", "groupId": group})
    return json.loads(response.text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)

    import_start = time()
    import_id = start_import(sample_audio, iv_group)
    logging.debug("Waiting for up to 30 minutes for import {} to complete...".format(import_id))
    timeout = time() + 60 * 30
    while 'finished' not in get_import_details(import_id) and time() < timeout:
        sleep(2)
    import_details = get_import_details(import_id)['importMetadataList'][0]


    item_id = import_details['importItems'][0]['item_id']
    item_details = get_item_details(item_id, iv_group)

    logging.info("item {} from import {} was processed in {} seconds. {} words were transcribed."
                 .format(item_id, import_id, round(time() - import_start), len(item_details['srts'])))