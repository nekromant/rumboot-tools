import os
import time
import usb.core
import usb.util
from parse import parse
from rumboot.resetseq.resetSeqBase import base
from requests import post

class hass(base):
    name = "HomeAssistant Switch"
    swap   = False
    supported = ["POWER", "RESET", "HOST"]
    mapping = {
        #defaults to a test switch
        "POWER" : None,
        "RESET" : None,
        "HOST"  : None
    }

    def __init__(self, terminal, opts):
        self.url   = opts["hass_server"]
        self.token = opts["hass_token"]
        self.mapping["POWER"] = opts["hass_power_switch"]
        self.mapping["RESET"] = opts["hass_reset_switch"]
        self.mapping["HOST"]  = opts["hass_host_switch"]

        super().__init__(terminal, opts)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.mapping[key] is None:
            return 

        if value:
            url = self.url + "/api/services/switch/turn_on"
        else:
            url = self.url + "/api/services/switch/turn_off"

        headers = {
            "Authorization": "Bearer " + self.token,    
            "content-type": "application/json",
        }

        data = '{"entity_id": "%s"}' % self.mapping[key]
        response = post(url, headers=headers, data = data)

    def get_options(self):
        return {
                "hass-power-switch" : {
                    "help" : "Home Assistant power switch",
                    "default" : "switch.0x00158d0002c7faa0",
                    "action"  : 'store_true'
                },
                "hass-reset-switch" : {
                    "help" : "Home Assistant reset switch",
                    "default" : False,
                },
                "hass-host-switch" : {
                    "help" : "Home Assistant host switch",
                    "default" : False,
                },
                "hass-token" : {
                    "help" : "Secret token",
                    # Defaults to a test token
                    "default" : "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJjZDUyMGYzZGUxZWQ0YTMzOWI4ZDY0ODQ3OWI0ZjE4ZiIsImlhdCI6MTYyOTU0NDg3NiwiZXhwIjoxOTQ0OTA0ODc2fQ.bJIj5VU_tNQLG6TXk1rkbA-BFpe0mYEsGfoWS4olzXs"
                },
                "hass-server" : {
                    "help" : "Hass server URL",
                    # Defaults to a test server
                    "default" : "http://homeblade:8123"
                }
            }