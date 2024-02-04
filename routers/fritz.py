from common.router import Router, Host
from typing import List

from fritzconnection.lib.fritzhosts import FritzHosts

class Fritz(Router):
    def __init__(self, host, port, user, password):
        super().__init__(host, port=port, user=user, password=password)
        self.fh = FritzHosts(address=host, user=user, password=password)

    def get_active_hosts(self) -> List[Host]:
        needed_keys = ['mac', 'name']
        hosts = []
        for host in self.fh.get_active_hosts():
            hosts.append({k:host[k] for k in needed_keys})
        return hosts
