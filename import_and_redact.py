import json
import logging

import requests
from time import sleep, time

iv_api = "https://iv-staging-1.chaseits.co.uk:8443/vrxServlet/v2"
login = ("tommy", "tomcat")  # see the admin guide or API docs for details on setting up API credentials
cert = '/opt/jumpto/ssl/ca-cert.pem'
iv_group = 5
sample_audio = 'http://http-ws.bbc.co.uk.edgesuite.net/mp3/learningenglish/2014/09/bbc_witn_cyclists_report_140915_witn_cycling_report_au_bb.mp3'


def start_import(audio_files_to_import, group):
    querystring = {"userId": "1", "groupId": group}
    import_selection = {"importFolder": audio_files_to_import, "modelId": 1,
                        "diarizationEnabled": False, "treatAllFilesAsSingleChannel": False}
    response = requests.post("{}/imports".format(iv_api), auth=login,
                             headers={"Content-Type": "application/json", "Accept": "application/json"},
                             json=import_selection, verify=cert, params=querystring)
    if response.status_code == requests.codes.ok:
        return json.loads(response.text)[u'importId']
    else:
        raise Exception('could not import audio. response was:{} {}'.format(response.status_code, response.text))


def get_import_details(import_id):
    response = requests.get('{}/imports/{}'.format(iv_api, import_id), auth=login, verify=cert, params={"userId": 1})
    return json.loads(response.text)


def get_item_details(item_id, group):
    querystring = {"userId": "1", "groupId": group}
    return json.loads(requests.get('{}/items/{}'.format(iv_api, item_id), auth=login, verify=cert, params=querystring))


def redact(group, item_id, inpoint, duration):
    redaction = {"inPoint": int(inpoint), "outPoint": int(inpoint) + int(duration), "type": 1, "redactedtext": ""}
    requests.post("{}items/{}/redactions".format(iv_api, item_id),
                  auth=login, json=redaction, verify=cert, params={"userId": "1", "groupId": group})


def download_redacted_file(group, item_id, output_file):
    recording = requests.get("{}items/{}/recording".format(iv_api, item_id), auth=login, verify=cert,
                             params={"userId": "1", "groupId": group, "recordingType": "redacted"})
    with open(output_file, 'wb') as f:
        f.write(recording.content)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    import_start = time()
    import_id = start_import(sample_audio, iv_group)

    logging.info("Waiting for up to 30 minutes for processing to complete...")
    timeout = time() + 60 * 30
    while not 'finished' in get_import_details(import_id) and time() < timeout:
        sleep(10)

    import_details = get_import_details(import_id)['importMetadataList'][0]
    logging.info("import {} complete in {} seconds".format(import_id, time() - import_start))
    item_id = import_details['importItems'][0]['item_id']
    item_details = get_item_details(item_id, iv_group)
    for srt in item_details['srts']:
        if srt['word'] in ['car', 'van']:
            redact(iv_group, item_id, srt['timestamp'], srt['length'])
    download_redacted_file(iv_group, item_id, '/tmp/{}_redacted.mp3'.format(item_id))
