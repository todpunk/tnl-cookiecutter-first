# -*- coding: utf-8 -*-
"""
This file contains views we can't currently get until we build such functionality into the UI and such shouldn't
exist in the final app, but great pains have been taken to make them safe for the interim
"""

from pyramid.httpexceptions import HTTPForbidden

def is_internal(request):
    """
    Return true if the request is internal
    """
    internal_hosts = ['localhost']
    # TODO: 172.2 is internal only if it's 2x, not 2xx, so more than should will get marked internal by this,
    # and this could use an efficiency upgrade anyway
    internal_address_starts = ['0.0.0.0', '127.0.0.1', '10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.', '172.2', '172.30.', '172.31.',]
    if request.host.split(':', 1)[0] not in internal_hosts or \
            any([request.remote_addr.startswith(x) for x in internal_address_starts]):
        return False
    return True

