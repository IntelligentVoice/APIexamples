#!/usr/bin/env python
# coding=utf-8
""" Code sample demonstrating batch audio ingestion with SFTP and 4.0.1 Intelligent Voice API
Code does 3 steps:
1. Create a new security group on the IV server using the REST API
2. Trigger the processing of the data using the REST API
3. Print a message when all processing is complete
"""
import json
import logging
from time import sleep, time

import requests
from requests.packages import urllib3

# FTP server where audio/csv files are
sftp_user = "chase"
sftp_password = "Obs1lon"
sftp_host = "iv-staging-1.chaseits.co.uk"
sftp_folder = "/home/chase/enron"
import_path = "sftp://{}:{}@{}:{}".format(sftp_user, sftp_password, sftp_host, sftp_folder)

# IV server which is going to process the files
iv_server = "iv-staging-1.chaseits.co.uk"
api_key = "tommy"
api_pass = "tomcat"
ws_path = "https://{}:8443/vrxServlet/ws/VRXService/vrxServlet".format(iv_server)

def create_new_group(group_name):
    """ Create a new group using the API"""
    logging.info('Creating new group "{}"...'.format(group_name))
    response = requests.post("{}/CreateNewGroup".format(ws_path), auth=(api_key, api_pass),
                             headers={"Content-Type" : "application/json", "Accept" : "application/json"},
                             json={"newGroup" : {"name" : group_name}}, verify=False)
    try:
        return json.loads(response.text)[u'newGroup'][u'client']
    except KeyError:
        logging.error("could not create group. response was:{}".format(response.text))

def start_import(audio_files_to_import, group):
    """ Bulk import audio files from a path on the IV server.  If any .csv files are found, matching files will be
    imported with their metadata.  If no .csv files are found, all audio files are imported, without metadata"""
    import_selection = {"ImportSelection": {"importFolder": audio_files_to_import, "client": group, "modelId" : 1, "userId" : 1, "diarizationEnabled" : False}}
    response = requests.post("{}/ImportFolders".format(ws_path), auth=(api_key, api_pass),
                             headers={"Content-Type" : "application/json", "Accept" : "application/json"},
                             json=import_selection, verify=False)
    if (response.status_code == requests.codes.ok):
        return json.loads(response.text)[u'ImportSelection'][u'importSelectionId']
    else:
        raise Exception('could not import audio. response was:{}'.format(response.text))

def get_import_details(id):
    response = requests.get('{}/getImportDetails/{}'.format(ws_path, id), auth=(api_key, api_pass), verify=False)
    return json.loads(response.text)[u'ImportJob']

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    logging.getLogger("paramiko").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    urllib3.disable_warnings()
    logging.info("starting up")

    # create a new security group to contain the audio data
    new_group = create_new_group("example Group")
    logging.info("new group is {}".format(new_group))

    import_start = time()
    import_id = start_import(import_path, new_group)

    logging.info("Waiting for up to 30 minutes for processing to complete...")
    timeout = time() + 60 * 30
    while 'finished' not in get_import_details(import_id) and time() < timeout:
        sleep(10)

    import_details = get_import_details(import_id)
    logging.info("processing complete in {}".format(time() - import_start))