#!/usr/bin/python3
from netmiko import ConnectHandler, ssh_exception
from paramiko.ssh_exception import SSHException
from getpass import getpass
import subprocess
import sys
import smtplib
import time
import csv
import os

timestr = time.strftime("%Y%m%d")
filename = "vpnusers_"+timestr+".csv"

user = 'username'
passwd = 'password'
hostname = 'gwaddress'

mkfwext1 = {
    'device_type': 'checkpoint_gaia',
    'ip': hostname,
    'username': user,
    'password': passwd,
}

try:
    net_connect = ConnectHandler(**mkfwext1)
except SSHException as e:#replace with netmiko exception
    print("Can't connect to device {},\n{}".format(hostname, e))
    sys.exit(1)
except ssh_exception.NetMikoTimeoutException as e:
    print("Timeout for device {},\n{}".format(hostname, e))
    sys.exit(1)
except ssh_exception.NetMikoAuthenticationException as e:
    print("Invalid Credentials for device {},\n{}".format(hostname, e))
    sys.exit(1)

output = net_connect.send_command("fw tab -t userc_users -s")
lines = output.split('\n')
for line in lines:
    if 'NAME' in line:
        continue
    vars = line.split()
    vals = vars[3]
    peak = vars[4]
    print ("Current Remote Users: ",vals)
    print ("Peak number of users:", peak)
net_connect.disconnect()

#timestr = time.strftime("%Y%m%d_%H%M")
timestr = str(time.strftime("%H:%M %d/%m/%Y"))

recipients = "user1@address,user2@address,user3@address"
TO = recipients.split(',')
SUBJECT = 'VPN users report'
TEXT = "Date and Time: {}\nCurrent Remote Users: {}\nPeak Number of users: {}".format(timestr, vals, peak)

# exchange Sign In
exchange_sender = 'echangeuser@address'
exchange_passwd = 'exchangepassword'

server = smtplib.SMTP('smtps-server', 25)
server.ehlo()
server.starttls()
server.login(exchange_sender, exchange_passwd)

BODY = '\r\n'.join(['To: %s' % TO,
                    'From: %s' % exchange_sender,
                    'Subject: %s' % SUBJECT,
                    '', TEXT])
try:
    server.sendmail(exchange_sender, TO, BODY)
    print ('email sent')
except:
    print ('error sending mail')

server.quit()

if os.path.isfile(filename):
    vpnusersfile = open(filename, 'a')
    csvwriter = csv.writer(vpnusersfile)
else:
    vpnusersfile = open(filename, 'w')
    csvwriter = csv.writer(vpnusersfile)
    header = ["Time", "VpnUsers", "PeakUsers"]
    csvwriter.writerow(header)

hrsandmins =  str(time.strftime("%H:%M"))
new_row = [hrsandmins, vals, peak]
csvwriter.writerow(new_row)
vpnusersfile.close()
