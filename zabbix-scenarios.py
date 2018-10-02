'''
This script is for create webcheck scenarios and triggers (failed and response time)
read options from file with below format per line, Each option splited by (,)
[scenario_name,url_check,step_name,status,severity,last_avg_count,Response_time,Failed_count_avg]
command run in bash:
            python zabbix-scenarios.py  -u [admin_user] -p [password] -f [File_path]
'''

from pyzabbix import ZabbixAPI
import sys
from optparse import OptionParser
from importlib import reload
reload(sys)

parser = OptionParser()
parser.add_option('-u', '--user', dest='user', help='User for authentication', metavar='USER')
parser.add_option('-p', '--password', dest='password', help='Password for authentication', metavar='PASSWORD')
parser.add_option('-f', '--file', dest='filename', help='File with Name,URL', metavar='FILE')

(options, args) = parser.parse_args()

group='Zabbix server'
hostid=10084
applicationid=1058
step_name=''
severity=4
resp_count=5
resp_time=0.6
failed_count=3
server_url='http://127.0.0.1'
user=options.user
password=options.password
filename=options.filename
if server_url and user and password:
    ZABBIX_SERVER = server_url
    zapi = ZabbixAPI(ZABBIX_SERVER)
    zapi.login(user,password)

else:
    print('user and password are required')
    sys.exit(1)


file_to_parse = open(filename, 'r')
for line in file_to_parse:
    if not line.startswith('#'):
        values = line.split(',')
        try :
            name = values[0]
            url = values[1]
            step_name = values[2]
        except IndexError as e:
            print('Need at minimun 3 params Traceback %s:' % e)
            sys.exit(1)
        try :
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



        request = zapi.do_request('httptest.get', params={"filter": {"name": name}})


        if request['result']:
            print('Host "%s" already registered' % name)
            sys.exit(1)
        else:

              zapi.do_request('httptest.create', params={"name": name,"hostid": hostid,"applicationid": applicationid, "delay": '1m',"retries": '1', "steps": [ { 'name': step_name, 'url': url,'status_codes': status, 'no': '1'} ] } )

              zapi.do_request('trigger.create', params={
                "description": name,
                "comments": 'The website below does not response the HTTP request ( visit website member ) at least %s, this warning means that the website is down or unstable.\n%s' % (failed_count,url),
                "expression": '{%s:web.test.fail[%s].min(#%s)}>0' % (group, name,failed_count), "priority": severity,
              })

              zapi.do_request('trigger.create', params={
                "description": name,
                "comments": 'The website below has High response Time request ( visit website member ) , this warning means that the website is down or unstable.\n%s' % url,
                "expression": '{%s:web.test.time[%s,%s,resp].min(#%s)}>%s' % (group, name, step_name,resp_count,resp_time), "priority": 4
              })
file_to_parse.close()