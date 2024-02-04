from common.router import Router, Host
from typing import List
import requests
import time
import hashlib
from xml.etree import ElementTree


class Zte(Router):
    def __init__(self, host, port, user, password):
        super().__init__(host=host, port=port, user=user, password=password)
        self.time = int(time.time()*1000) 
    
    def _login(self):
        first = requests.get(f'http://{self.host}:{self.port}/?_type=loginData&_tag=login_token&_={self.time}')
        cookie = (first.headers.get('Set-Cookie', '').split(';')[0])
        login_token = first.text.split('>')[1].split('<')[0]

        sess_response = requests.get(f"http://{self.host}:{self.port}/?_type=loginData&_tag=login_entry&_={self.time}",headers={'Cookie': cookie})
        sess_token = sess_response.json()['sess_token']

        hashed_password = hashlib.sha256((self.password + login_token).encode('utf-8')).hexdigest()
        session = requests.Session()
        result = session.post(
            f'http://{self.host}:{self.port}',
            params={'_type': 'loginData', '_tag': 'login_entry'},
            headers={
                'Cookie': cookie,
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': f"http://{self.host}:{self.port}",
                'Pragma': 'no-cache',
                'Referer': f"http://{self.host}:{self.port}",
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            },
            data={
                'action': 'login',
                'Password': hashed_password,
                'Username': self.user,
                '_sessionTOKEN': sess_token,
            }
        )
        auth_cookie = (result.headers.get('Set-Cookie', '')).split('=')[1].split(';')[0]
        return session

    def _get_active_hosts(self) -> List:
        hosts = []
        session = self._login()
        first = session.get(f'http://{self.host}:{self.port}/?_type=menuView&_tag=lanMgrIpv4&Menu3Location=0&_={self.time}')    
        if not first.ok:
            print('TODO error')
        dhcp_addresses = session.get(f'http://{self.host}:{self.port}/?_type=menuData&_tag=dhcp4s_dhcphostinfo_m.lua&_={self.time}')                     
        if not dhcp_addresses.ok:
            print('TODO error')
        
        dhcp_xml = ElementTree.fromstring(dhcp_addresses.content)
        mac_ip_name = []
        next_ip = False
        next_mac = False
        next_name = False
        for instance in dhcp_xml.findall('.//Instance'):
            name = ''
            mac_address = ''
            ip_address = ''
            for attribute in instance.iter():
                if next_ip:
                    ip_address = attribute.text
                    next_ip = False
                if next_mac:
                    mac_address = attribute.text
                    next_mac = False
                if next_name:
                    name = attribute.text
                    next_name = False
                if attribute.text == 'OBJ_DHCPHOSTINFO_ID.IPAddr' and attribute.tag == 'ParaName':
                    next_ip = True
                if attribute.text == 'OBJ_DHCPHOSTINFO_ID.MACAddr' and attribute.tag == 'ParaName':
                    next_mac = True
                if attribute.text == 'OBJ_DHCPHOSTINFO_ID.HostName' and attribute.tag == 'ParaName':
                    next_name = True
            mac_ip_name.append({'name': name, 'mac': mac_address, 'ip': ip_address})

        first = session.get(f'http://{self.host}:{self.port}/?_type=menuView&_tag=arpTable&Menu3Location=0&_={self.time}')
        if not first.ok:
            print('TODO error')
        arp_table = session.get(f'http://{self.host}:{self.port}/?_type=menuData&_tag=arp_arptable_lua.lua&_={self.time}')
        if not arp_table.ok:
            print('TODO error')

        arp_xml = ElementTree.fromstring(arp_table.content)
        ip_status = []
        next_ip = False
        next_status = False
        for instance in arp_xml.findall('.//Instance'):
            status = None
            ip_address = ''
            for attribute in instance.iter():
                if next_ip:
                    ip_address = attribute.text
                    next_ip = False
                if next_status:
                    if attribute.text == '0':
                        status = False
                    elif attribute.text == '1':
                        status = True
                    next_status = False
                if attribute.text == 'DestIP' and attribute.tag == 'ParaName':
                    next_ip = True
                if attribute.text == 'Status' and attribute.tag == 'ParaName':
                    next_status = True
            ip_status.append({'ip': ip_address, 'status': status})

        online_filter = (x for x in ip_status if x['status'] == True) 
        for online in online_filter:
            join_ip = (x for x in mac_ip_name if x['ip'] == online['ip'])
            for filtered in join_ip:
                real = filtered
            hosts.append({'mac': real['mac'].upper(), 'name': real['name'], 'ip': online['ip'] })
        return hosts

    def get_active_hosts(self) -> List[Host]:
        needed_keys = ['mac', 'name']
        hosts = []
        for host in self._get_active_hosts():
            hosts.append({k:host[k] for k in needed_keys}) 
        return hosts
