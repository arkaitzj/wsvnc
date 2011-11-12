WSVNC
=====

Tunnel VNC through a WebSocket and use it with plain Javascript client from your HTML5 browser

Works on Firefox 7.0.1 and Chrome 15.0

INSTALL
-------
    virtualenv --no-site-packages sandbox && sandbox/bin/pip install -r requirements.txt

RUN
---
    sandbox/bin/python wsvnc.py

REUSED SOFTWARE
---------------

Most of the HTML and Javascript side comes from 
https://github.com/vti/showmethedesktop

The RFB implementation has reused most of:
http://code.google.com/p/python-vnc-viewer/
