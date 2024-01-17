import time
import datetime
import itertools

from fritzconnection.lib.fritzhosts import FritzHosts
from fritzconnection.core.exceptions import FritzServiceError

import os
import requests
from dotenv import load_dotenv
load_dotenv()

ADDRESS = os.getenv('FRITZ_URL','192.168.178.1')
USER = os.getenv('FRITZ_USER')
PASSWORD = os.getenv('FRITZ_PASSWORD')
MAC_ADDRESS_WHITELIST = [mac_address for mac_address in os.getenv('MAC_ADDRESS_WHITELIST').split(',')]

TRACKING_INTERVAL = 60 # 60 seconds
QBIT_AUTOMATION_WEBPAGE_ENDPOINT = os.getenv('QBIT_AUTOMATION_WEBPAGE_ENDPOINT')

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
QBIT_SPEED_TOGGLE_ENDPOINT = os.getenv('QBIT_SPEED_TOGGLE_ENDPOINT')
QBIT_SPEED_TOGGLE_STATE_ENDPOINT = os.getenv('QBIT_SPEED_TOGGLE_STATE_ENDPOINT')

def send_notification(message, url = DISCORD_WEBHOOK_URL):
    data = {
        "content": message,
        "username": "Qbit speed toggle",
    }

    headers = {
        "Content-Type": "application/json"
    }

    result = requests.post(url, json=data, headers=headers)
    if 200 <= result.status_code < 300:
        print(f"Discord notification sent {result.status_code}")
    else:
        print(f"Discord notification not sent with {result.status_code}, response:\n{result.json()}")
    return

def toggle_speed(is_limited, url = QBIT_SPEED_TOGGLE_ENDPOINT):
    result = requests.post(url)
    if 200 <= result.status_code < 300:
        if is_limited == True:
            message = f"Removing speed limit"
        else:
            message = f"Enabling speed limit"
        print(message)
        send_notification(message)
        return True
    else:
        print(f"Unable to toggle speed error code {result.status_code}, response:\n{result.json()}")
        send_notification(f"Unable to toggle speed error code {result.status_code}, response:\n{result.json()}")
    return False

def is_speed_limit_enabled(url = QBIT_SPEED_TOGGLE_STATE_ENDPOINT):
    result = requests.get(url)
    if result.status_code >= 300:
        send_notification("Unable to get current speed limit state")
        return None
    if result.text == '1':
        return True
    else:
        return False
    
def get_speed_toggle_setting():
    try:
        return requests.get(QBIT_AUTOMATION_WEBPAGE_ENDPOINT).json()['value']
    except:
        send_notification("Unable to get webpage radio button value")
        return '1'

def check_devices(interval):
    fh = FritzHosts(address=ADDRESS, user=USER, password=PASSWORD)
    while True:
        new_mac_found = False
        speed_toggle = get_speed_toggle_setting()
        mac_dict = {}
        if speed_toggle == '2' or speed_toggle == '3':
            hosts = fh.get_active_hosts()
            for host in hosts:
                if not host['mac']:
                    continue
                mac = host['mac']
                name = host['name']
                if mac not in MAC_ADDRESS_WHITELIST:
                    new_mac_found = True
                    mac_dict[mac] = name 
            
            is_limited = is_speed_limit_enabled()
            if new_mac_found:
                if is_limited == False:
                    toggle_speed(is_limited)
                    for mac, name in mac_dict.items():
                        print(f'new host found {name} with MAC {mac}')
            else:
                if speed_toggle == '3':
                    if is_limited == True:
                        toggle_speed(is_limited)
        time.sleep(interval)
 

def main():
    check_devices(TRACKING_INTERVAL)


if __name__ == '__main__':
    main()
