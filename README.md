Zabbix-web-scenario
===================

Script to make a web scenario and a trigger with zabbix api in python3.

Syntax of options in file:
	[scenario_name,url_check,step_name,status,severity,last_avg_count,Response_time$]
	In list file per line commented by '#' and all of options is mandatory.


Command run in bash:
       python zabbix-scenarios.py  -u [admin_user] -p [password] -f [File_path]
