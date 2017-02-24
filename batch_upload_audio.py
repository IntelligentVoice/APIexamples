#!/usr/bin/env python
# coding=utf-8
""" Code sample demonstrating batch audio ingestion with SFTP and the Intelligent Voice API
Code does 4 steps:
1. Create a new security group on the IV server using the REST API
2. Upload data to IV server using SFTP
3. Trigger the processing of the data using the REST API
4. Print a message when all processing is complete
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import json
import logging
from time import sleep, time

import requests
from fabric.api import env, sudo, put, hide
from requests.packages import urllib3

folder_containing_audio_and_csv = "C:\\Data\\enron"
audio_data_folder_on_iv_server = "/data/enron"
temp_folder = "C:\\tmp\\enron-converted"

iv_server_fqdn = "iv.example.com"
self_signed_cert_path = "C:\\ssl\\ca-cert.pem"  # set to None if using real SSL cert

api_key = "api-user"
api_pass = ""

ssh_user = 'iv'
ssh_password = ""

ws_path = "https://{}:8443/vrxServlet/ws/VRXService/vrxServlet/".format(iv_server_fqdn)


def create_new_group(group_name):
    """ Create a new group using the API"""
    logging.info('Creating new group "{}"...'.format(group_name))
    response = requests.post("{}CreateNewGroup".format(ws_path), auth=(api_key, api_pass),
                             data=json.dumps({"name": group_name}), verify=self_signed_cert_path)
    try:
        return json.loads(response.text)[u'newGroup'][u'client']
    except KeyError:
        logging.error("could not create group. response was:{}".format(response.text))


def upload_audio(source_path, destination_path):
    """ SFTP is one method of making audio available on the IV Server.
    You could also use a network share, or connect removable storage to the server"""
    env.host_string = '{}@{}'.format(ssh_user, iv_server_fqdn)
    env.password = ssh_password
    with hide('output', 'running'):
        sudo('mkdir -p {}'.format(destination_path))
        sudo('chown {} {}'.format(ssh_user, destination_path))
        put(source_path, destination_path)


def start_import(audio_files_to_import, group):
    """ Bulk import audio files from a path on the IV server.  If any .csv files are found, matching files will be
    imported with their metadata.  If no .csv files are found, all audio files are imported, without metadata"""
    import_selection = {"ImportSelection": {"importFolder": audio_files_to_import, "client": group}}
    response = requests.post("{}ImportFolders".format(ws_path), auth=(api_key, api_pass),
                             data=json.dumps(import_selection), verify=self_signed_cert_path)
    try:
        return int(response.text)
    except ValueError:
        logging.error('could not import audio. response was:{}'.format(response.text))


def get_import_details(id):
    response = requests.get('{}getImportList'.format(ws_path), auth=(api_key, api_pass), verify=self_signed_cert_path)
    import_list = json.loads(response.text)
    for i in import_list['Imports']['import']:
        if int(i['id']) == id:
            return i
    return import_list


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    logging.getLogger("paramiko").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    urllib3.disable_warnings()
    logging.info("starting up")

    # create a new security group to contain the audio data
    new_group = create_new_group("example Group")
    logging.info("new group is {}".format(new_group))

    # upload the audio with SFTP
    upload_audio(folder_containing_audio_and_csv, audio_data_folder_on_iv_server)

    import_start = time()
    import_id = start_import(audio_data_folder_on_iv_server, new_group)

    logging.info("Waiting for up to 30 minutes for processing to complete...")
    timeout = time() + 60 * 30
    while 'finished' not in get_import_details(import_id) and time() < timeout:
        sleep(10)

    import_details = get_import_details(import_id)
    logging.info("processing complete in {}".format(time() - import_start))
