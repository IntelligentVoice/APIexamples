<?php /**
 * Demonstrates use of the getRecording and getDocument API calls to retrieve an audio file and associated metadata
 * from an Intelligent Voice server.  Metadata includes transcript, speaker separation data, word-level timing data
 * and included audio file metadata.
 *
 * A check is done to see if the recording file exists already on the server before fetching from the API.
 *
 * The metadata is in JSON format and is written into the HTML.  The creation of the interactive transcript is done
 * in Javascript.  Note: this is not the recommended way to do it - it would be be a better user experience to render
 * the HTML in the back end PHP.
 *
 * This example shows an video file but the same method works with audio
 * (various player options including embedded players or YouTube etc)
 */

// API connection settings - if you don't have these already contact Intelligent Voice for details
const IV_APP_SERVER = "";
const IV_APP_SERVER_PORT = 8443;
const API_KEY = '';
const API_PASSWORD = '';

const ITEM_ID = 31000000;
const GROUP = 31;

// Production servers should always have a valid SSL cert so these values should be set to 1
const CHECK_FOR_VALID_SSL_CERT = 0;
const CHECK_SSL_CERT_MATCHES_HOSTNAME = 0;

// Default installer will create self-signed certs using an IV created CA.
const CA_CERT = '/opt/jumpto/ssl/ca-cert.pem';
const SSL_CERT_TYPE = 'PEM';

ini_set('display_startup_errors', 1);
ini_set('display_errors', 1);
ini_set('log_errors', 1);
error_reporting(E_ALL | E_STRICT); /* download the audio file */
$filename = '/var/www/recordings/' . ITEM_ID . '.mp4';
if (!file_exists($filename)) {
    $url = sprintf("https://%s:%s@%s:%d/vrxServlet/ws/VRXService/vrxServlet/getVideo/%d/1/%d",
        API_KEY,
        API_PASSWORD,
        IV_APP_SERVER,
        IV_APP_SERVER_PORT,
        GROUP,
        ITEM_ID
    );
    error_log("getting " . $url);
    $fp = fopen($filename, 'w');
    error_log("writing to " . $filename);
    $ch = curl_init($url);
    $curl_opts = array(
        CURLOPT_HTTPHEADER => array('Accept: video/mp4'),
        CURLOPT_TIMEOUT => 10,
        CURLOPT_RETURNTRANSFER => 1,
        CURLOPT_FILE => $fp,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_SSL_VERIFYPEER => CHECK_FOR_VALID_SSL_CERT,
        CURLOPT_SSL_VERIFYHOST => CHECK_SSL_CERT_MATCHES_HOSTNAME,
        CURLOPT_VERBOSE => true
    );
    curl_setopt_array($ch, $curl_opts);
    $result = curl_exec($ch);
    curl_close($ch);
    fclose($fp);
}
$url = sprintf("https://%s:%s@%s:%d/vrxServlet/ws/VRXService/vrxServlet/getDocument/%d/1/%d",
    API_KEY,
    API_PASSWORD,
    IV_APP_SERVER,
    IV_APP_SERVER_PORT,
    GROUP,
    ITEM_ID);
$curl_opts = array(
    CURLOPT_HTTPHEADER => array('Accept: application/json'),
    CURLOPT_RETURNTRANSFER => 1,
    CURLOPT_SSL_VERIFYPEER => CHECK_FOR_VALID_SSL_CERT,
    CURLOPT_SSL_VERIFYHOST => CHECK_SSL_CERT_MATCHES_HOSTNAME
);
$ch = curl_init($url);
curl_setopt_array($ch, $curl_opts);
$response = curl_exec($ch);
$info = curl_getinfo($ch);
curl_close($ch);
if ($info['http_code'] != 200) {
    trigger_error($info['http_code'] . ' ' . $url);
}
?> <!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <script>
        var exported = <?= $response ?>;
    </script>
    <link rel="stylesheet" type="text/css" href="smarttranscript.css">
    <script>
        function scrollToView() {
            var a = document.getElementById("doc-scroller");
            var d = a.getElementsByClassName('highlight');
            if (d.length) {
                d = d[0];
                var scrollHeight = a.offsetHeight;
                var scrollOffset = a.scrollTop;
                var targetOffset = d.offsetTop;
                // Scroll into viewport only if out of bounds.
                if ((targetOffset > (scrollHeight + scrollOffset)) || (targetOffset < scrollOffset)) {
                    a.scrollTop = targetOffset - 20;
                }
            }
        }
        function getClosestValues(a, x) {
            var lo = -1, hi = a.length;
            while (hi - lo > 1) {
                var mid = Math.round((lo + hi) / 2);
                if (a[mid] <= x) {
                    lo = mid;
                } else {
                    hi = mid;
                }
            }
            if (a[lo] === x)
                hi = lo;
            return [a[lo], a[hi]];
        }
        function seek2(pos, offset) {
            if (!isNaN(offset)) {
                pos += offset;
                if (pos < 0) {
                    pos = 0;
                }
            }
            var mediaElement = document.getElementById('media_player');
            mediaElement.currentTime = pos / 1000;
            scrollToView();
        }
    </script>
</head>
<body>
<div class="ui-widget ui-widget-content" id="document-div">
    <table>
        <tr>
            <td>
                <div id="topics">
                    <h2><em>JumpTo</em> Topics</h2><br>
                    <div id="topics-container">
                        {{topics}}
                    </div>
                </div>
            </td>
            <td id="table_1">
                <div id="doc-main">
                    <div id="exported_from">{{from}}</div>
                    <div id="exported_to">{{to}}</div>
                    <div id="exported_timestamp">{{timestamp}}</div>
                    <h1 id="exported_title">{{title}}</h1>
                    <video id="media_player" controls></video>
                    <!-- <div id="position"></div> -->
                    <div style="position:relative;" id="doc-scroller"><br>
                        {{body}}
                    </div>
                </div>
            </td>
        </tr>
    </table>
</div>
<script>
    var media_player = document.getElementById('media_player'),
        current_links = [],
        linkers = [];
    document.addEventListener('DOMContentLoaded', function () {
        media_player.play(); // Auto-buffer.
        media_player.pause();
        media_player.addEventListener("timeupdate", function () {
            for (var i = 0; i < current_links.length; i++) {
                if (!isNaN(current_links[i])) {
                    document.getElementById("position_" + current_links[i]).className = "";
                }
            }
            var g = getClosestValues(linkers, media_player.currentTime * 1000);
            current_links = g;
            var a = document.getElementById("doc-scroller");
            for (var i = 0; i < g.length; i++) {
                if (!isNaN(g[i])) {
                    var d = document.getElementById("position_" + g[i]);
                    if (d != null) {
                        d.className = "highlight";
                        scrollToView();
                    }
                }
            }
        });
    });
    // @body
    var body = '',
        spkr = 0;
    if ('SRTs' in exported['Item']) {
        console.log('srts count ' + exported['Item']['SRTs'].length)
        for (s = 0; s < exported['Item']['SRTs'].length; s++) {
            if ('words' in exported['Item']['SRTs'][s]) {
                var words_count = exported['Item']['SRTs'][s]['words'].length;
                console.log('words count ' + words_count)
                for (w = 0; w < words_count; w++) {
                    if (words_count >= 1) {
                        var word = exported['Item']['SRTs'][s]['words'][w],
                            text = word.word,
                            timestamp = Math.round(word.timestamp * 1000),
                            colour = 0;
                    } else {
                        var word = exported['Item']['SRTs'][s]['words'],
                            text = word.word,
                            timestamp = Math.round(word.timestamp * 1000),
                            colour = 0;
                    }
                    if (spkr != word.speakerNo) {
                        body += '<br /><span class="label" data-speaker="' + word.speakerNo + '">' +
                            word.speakerLabel + ': </span> ';
                    }
                    if (text == 'REDACTED') {
                        text = '<span class="redacted">' + text + '</span>';
                        if (w > 0 && exported['Item']['SRTs'][s]['words'][w - 1]['word'] == 'REDACTED') {
                            text = '';
                        }
                    }
                    body += '<span id="position_' + timestamp + '" onclick="seek2(' + timestamp + ');"' +
                        ' style="color:rgb(' + colour + ',' + colour + ',' + colour + ')">' + text + '</span> ';
                    spkr = word.speakerNo;
                    linkers.push(timestamp);
                }
            } else {
                console.log('words not found')
            }
        }
    } else {
        console.log('srts not found')
    }
    // @topics
    var topics = '';
    if ('tags' in exported['Item'] && exported['Item']['tags'] != null && 'tags' in exported['Item']['tags']) {
        for (t = 0; t < exported['Item']['tags']['tags'].length; t++) {
            var tag = exported['Item']['tags']['tags'][t];
            if ('position' in tag) {
                if (tag.position.length > 1) {
                    var inline = [];
                    for (p = 0; p < tag.position.length; p++) {
                        var timestamp = Math.round(tag.position[p].timestamp * 1000);
                        if (p == 0) {
                            topics += '<a class="topics" href="javascript:seek2(' + timestamp + ', -5000);">' + tag.tag +
                                '</a>';
                        } else {
                            inline.push('<a class="topics" href="javascript:seek2(' + timestamp + ', -5000);">' +
                                tag.position[p].order + '</a>');
                        }
                        if (p == (tag.position.length - 1)) {
                            topics += ' (' + inline.join(', ') + ')<br />';
                        }
                    }
                } else if (tag.position.length === 1) {
                    var timestamp = Math.round(tag.position[0].timestamp * 1000);
                    topics += '<a class="topics" href="javascript:seek2(' + timestamp + ', -5000);">' + tag.tag + '</a><br> ';
                }
            }
        }
    }
    document.getElementById('exported_from').innerHTML = exported['Item']['from'];
    document.getElementById('exported_to').innerHTML = exported['Item']['to'];
    document.getElementById('exported_timestamp').innerHTML = exported['Item']['timestamp'];
    document.getElementById('exported_title').innerHTML = exported['Item']['title'];
    document.getElementById('topics-container').innerHTML = topics;
    document.getElementById('doc-scroller').innerHTML = body;
    document.getElementById('doc-main').getElementsByTagName('video')[0].innerHTML = '<source src="/recordings/<?= ITEM_ID .
    '.mp4' ?>" type="video/mp4">'; </script>
</body>
</html>
