#!/usr/bin/env python
# coding=utf-8
""" Code sample demonstrating redacting audio file using Intelligent Voice API v2 (available from V4.0)
Code does 3 steps:
1. Import an audio file from a URL
2. Redact the words 'car' and 'van' wherever they are found
3. Downloaded the redacted version of the audio file
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
                        "diarizationEnabled": False, "treatAllFilesAsSingleChannel": True}
    response = requests.post("{}/imports".format(iv_api), auth=login,
                             headers={"Content-Type": "application/json", "Accept": "application/json"},
                             json=import_selection, verify=cert, params={"userId": "1", "groupId": group})
    return json.loads(response.text)[u'importId']


def get_import_details(import_id):
    response = requests.get('{}/imports/{}'.format(iv_api, import_id), auth=login, verify=cert, params={"userId": 1})
    return json.loads(response.text)


def get_item_details(item_id, group):
    params = {"userId": "1", "groupId": group}
    return json.loads(requests.get('{}/items/{}'.format(iv_api, item_id), auth=login, verify=cert, params=params).text)


def redact(group, item_id, inpoint, duration):
    params = {"userId": "1", "groupId": group}
    redaction = {"inPoint": inpoint*1000, "outPoint": inpoint*1000 + duration*1000, "type": 1, "redactedText": ""}
    response = requests.post("{}/items/{}/redactions".format(iv_api, item_id), auth=login, json=redaction, verify=cert, params=params)


def download_redacted_file(group, item_id, output_file):
    recording = requests.get("{}/items/{}/recording".format(iv_api, item_id), headers={"Accept": "audio/wav"},
                             params={"userId": "1", "groupId": group, "recordingType": "redacted" }, auth=login, verify=cert)
    with open(output_file, 'wb') as f:
        f.write(recording.content)
    logging.debug("redacted file downloaded to {}".format(output_file))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)

    import_start = time()
    import_id = start_import(sample_audio, iv_group)

    logging.info("Waiting for up to 30 minutes for processing to complete...")
    timeout = time() + 60 * 30
    while 'finished' not in get_import_details(import_id) and time() < timeout:
        sleep(2)

    import_details = get_import_details(import_id)['importMetadataList'][0]
    logging.info("import {} complete in {} seconds".format(import_id, time() - import_start))
    item_id = import_details['importItems'][0]['item_id']
    item_details = get_item_details(item_id, iv_group)
    for srt in item_details['srts']:
        if srt['word'].lower() in ['car'.lower(), 'van'.lower()]:
            redact(iv_group, item_id, srt['timestamp'], srt['length'])

    download_redacted_file(iv_group, item_id, '/tmp/{}_redacted.wav'.format(item_id))
