"""
This script is for create webcheck scenarios and triggers (failed and response time)
read options from file with below format per line, Each option splited by (,)
[scenario_name,url_check,step_name,status,severity,last_avg_count,Response_time,Failed_count_avg]
command run in bash:
            python webcheck.py  -u [admin_user] -f [File_path] -g [zabbix_hostname]
"""

import getpass
import sys
from optparse import OptionParser

from pyzabbix import ZabbixAPI


def create_webcheck(self, w_name, w_hostid, w_applicationid, w_step_name, w_url, w_status):
    self.do_request('httptest.create',
                    params={"name": w_name, "hostid": w_hostid, "applicationid": w_applicationid, "delay": '1m',
                            "retries": '2',
                            "steps": [{'name': w_step_name, 'url': w_url, 'status_codes': w_status, 'no': '1'}]})


def create_trriger(self, t_name, t_failed_count, t_url, t_group, t_step_name, t_resp_count, t_resp_time, t_severity):
    self.do_request('trigger.create', params={
        "description": t_name,
        "comments": 'The website below does not response the HTTP request ( visit website member ) at least %s, this warning means that the website is down or unstable.\n%s' % (
            t_failed_count, t_url),
        "expression": '{%s:web.test.fail[%s].min(#%s)} > 0' % (t_group, t_name, t_failed_count), "priority": t_severity
    })
    print(t_resp_time)
    self.do_request('trigger.create', params={
        "description": t_name,
        "comments": 'The website below has High response Time request ( visit website member ), this warning means that the website is down or unstable.\n%s' % t_url,
        "expression": '{%s:web.test.time[%s,%s,resp].min(#%s)} > %s' % (
            t_group, t_name, t_step_name, t_resp_count, t_resp_time), "priority": t_severity
    })


def update_webcheck_triggers(self, uw_name, uw_step_name, uw_url, uw_status, uw_hostid, uw_applicationid, uw_group,
                             uw_failed_count, uw_resp_count, uw_resp_time, uw_severity):
    httptestid = self.do_request('httptest.get', params={"output": "httptestid", "filter": {"name": uw_name}})
    httptestid = httptestid['result'][0]['httptestid']
    self.do_request('httptest.delete', params={"httptestid": httptestid})

    self.do_request('httptest.create',
                    params={"name": uw_name, "hostid": uw_hostid, "applicationid": uw_applicationid, "delay": '1m',
                            "retries": '2',
                            "steps": [{'name': uw_step_name, 'url': uw_url, 'status_codes': uw_status, 'no': '1'}]})

    self.do_request('trigger.create', params={
        "description": uw_name,
        "comments": 'The website below does not response the HTTP request ( visit website member ) at least %s, this warning means that the website is down or unstable.\n%s' % (
            uw_failed_count, uw_url),
        "expression": '{%s:web.test.fail[%s].min(#%s)} > 0' % (uw_group, uw_name, uw_failed_count),
        "priority": uw_severity
    })
    # print(t_resp_time)
    self.do_request('trigger.create', params={
        "description": uw_name,
        "comments": 'The website below has High response Time request ( visit website member ), this warning means that the website is down or unstable.\n%s' % uw_url,
        "expression": '{%s:web.test.time[%s,%s,resp].min(#%s)} > %s' % (
            uw_group, uw_name, uw_step_name, uw_resp_count, uw_resp_time), "priority": uw_severity
    })


parser = OptionParser()
parser.add_option('-u', '--user', dest='user', help='User for authentication', metavar='USER')
parser.add_option('-a', '--url-address', dest='server_url', help='Server URL for connect to zabbix api',
                  metavar='SERVER_URL')
parser.add_option('-f', '--file', dest='filename', help='File with Name,URL', metavar='FILE')
parser.add_option('-g', '--hostname', dest='group', help='Name of the host for create scenarios', metavar='HOSTNAME')
(options, args) = parser.parse_args()

if not options.server_url:
    server_url = 'http://127.0.0.1'
user = options.user
password = getpass.getpass('Enter your password: ')
filename = options.filename
group = options.group
if server_url and user and group and password:

    zapi = ZabbixAPI(server_url)
    zapi._login(user, password)
    hst = zapi.do_request('host.get', {'output': ['hostid'], 'filter': {'host': group}})
    hostid = hst['result'][0]["hostid"]
    app = zapi.do_request('application.get', {"output": "extend", "hostids": hostid, "filter": {"name": "web checks"}})
    applicationid = app['result'][0]['applicationid']

else:
    print('user and password are required')
    sys.exit(1)

request = zapi.do_request('httptest.get', params={"filter": {}})
# print(request['result'][1])
http_list_items = list()
for x in request['result']:
    http_list_items.append(x['name'])
# print(http_list)
file_to_parse = open(filename, 'r')
for line in file_to_parse:
    print(line)
    if not line.startswith('#'):
        values = line.split(',')
        try:
            name = values[0]
            url = values[1]
            step_name = values[2]
        except IndexError as e:
            print('Need at minimun 3 params Traceback %s:' % e)
            sys.exit(1)
        try:
            status = values[3]
        except IndexError as e:
            status = '200'
        try:
            severity = values[4]
        except IndexError as e:
            severity = 4
        try:
            resp_count = values[5]
        except IndexError as e:
            resp_count = 5
        try:
            resp_time = values[6]
        except IndexError as e:
            resp_time = 0.6
        try:
            failed_count = values[7]
        except IndexError as e:
            failed_count = 3

        if name in http_list_items:
            print("name: exist", name)
            update_webcheck_triggers(zapi,name,step_name,url,status,hostid,applicationid,group,failed_count,resp_count,resp_time,severity)
        else:
            print("name:", name)
            create_webcheck(zapi, name, hostid, applicationid, step_name, url, status)
            create_trriger(zapi, name, failed_count, url, group, step_name, resp_count, resp_time, severity)

file_to_parse.close()
