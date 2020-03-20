#!/usr/bin/python3

"""
This plugin can get the number of vpn users from a checkpoint gaia gateway.
That number is checked against the number of warning and critical level users.
If the number is lower than the warning level number, an OK status is returned
If the number is higher than warning but lower than critical, a WARNING status is returned.
If the number is higher than critical, a CRITICAL status is returned.
In any case, the number of users is also returned.
execute as follows: ./check_vpn_users.py -H <hostname or ip> -u <user> -p <password> 
-w <no of users for warning level> -c <no of users for critical level>
you need to create a custom command like this:
####################################
# checkpoint check vpn users command
####################################
define command{
        command_name    check_vpn_users
        command_line    $USER1$/check_vpn_users.py -H $HOSTADDRESS$ -u $ARG1$ -p $ARG2$ -w $ARG3$ -c $ARG4$
}
and then a nagios service
"""

from netmiko import ConnectHandler, ssh_exception
from paramiko.ssh_exception import SSHException
#from getpass import getpass
import subprocess
import argparse

__author__ = "Ioannis Theodoridis"
__version__ = "1.0"
__email__ = "itheodoridis@bankofgreece.gr"
__licence__ = "MIT"
__status__ = "Production"

class VpnUserChecker:
    STATUS_OK = 0
    STATUS_WARNING = 1
    STATUS_CRITICAL = 2
    STATUS_UNKNOWN = 3

    def __init__(self):
        self.status = None
        self.messages = []
        self.perfdata = []
        self.options = None
        self.vpnusers = 0


    def run(self):
        self.parse_options()


        self.get_vpn_users()
        self.compare_users()

        self.print_output()

        return self.status

    def parse_options(self):
        parser = argparse.ArgumentParser(
            description="Monitoring check plugin to check number of Checkpoint Gaia VPN users."
                        "If the number is above warning level, the status is raised to WARNING. "
                        "If the number is above critical level, the status is CRITICAL."
                        "UNKNOWN is returned if there is a failure."
        )

        parser.add_argument("-H", "--hostname",
                            type=str, help="Hostname or ip-address")
        parser.add_argument("-u", "--user",
                            type=str, help="Gaia user name")
        parser.add_argument("-p", "--password",
                            type=str, help="Gaia user password")
        parser.add_argument("-w", "--warning",
                            type=int, help="Warning level for number of VPN users")
        parser.add_argument("-c", "--critical",
                            type=int, help="Critical level for number of VPN users")

        self.options = parser.parse_args()

        if not self.are_options_valid():
            print("Run with --help for usage information")
            print("")
            exit(0)

    def are_options_valid(self):
        if not self.options.hostname:
            print("You must specify a hostname")
            return False
        if not self.options.user:
            print("You must specify a user name")
            return False
        if not self.options.password:
            print("You must specify a user password")
            return False
        if not self.options.warning:
            print("You must specify a valid number of users for warning level")
            return False
        if not self.options.critical:
            print("You must specify a valid number of users for critical level")
            return False
        if self.options.critical <= self.options.warning:
            print("warning number of users must be less than critical number of users")
            return False
        return True

    def print_output(self):
        """ Prints the final output (in Nagios plugin format if self.status is set)
        :return:
        """
        output = ""
        if self.status == self.STATUS_OK:
            output = "OK"
        elif self.status == self.STATUS_WARNING:
            output = "Warning"
        elif self.status == self.STATUS_CRITICAL:
            output = "Critical"
        elif self.status == self.STATUS_UNKNOWN:
            output = "Unknown"

        if self.messages:
            if len(output):
                output += " - "
            # Join messages like sentences. Correct those messages which already ended with a period or a newline.
            output += ". ".join(self.messages).replace(".. ", ".").replace("\n. ", "\n")

        if self.perfdata:
            if len(output):
                output += " | "
            output += " ".join(self.perfdata)

        print(output)

    def get_vpn_users(self):
        #user = input('username:')
        #passwd = getpass()

        mkfwext1 = {
            'device_type': 'checkpoint_gaia',
            'ip': self.options.hostname,
            'username': self.options.user,
            'password': self.options.password,
            }

        try:
            net_connect = ConnectHandler(**mkfwext1)
        except SSHException as e:#replace with netmiko exception
            #self.add_status(self.STATUS_UNKNOWN)
            print("can't connect to device {}, {}".format(self.options.hostname, e))
            sys.exit(1)
        except ssh_exception.NetMikoTimeoutException as e:
            #self.add_status(self.STATUS_UNKNOWN)
            print("Timeout for device {}, {}".format(self.options.hostname, e))
            sys.exit(1)
        except ssh_exception.NetMikoAuthenticationException as e:
            #self.add_status(self.STATUS_UNKNOWN)
            print("Invalid Credentials for device {}, {}".format(self.options.hostname, e))
            sys.exit(1)

        output = net_connect.send_command("fw tab -t userc_users -s")
        lines = output.split('\n')
        for line in lines:
            if 'NAME' in line:
                continue
            vars = line.split()
            vals = vars[3]
            peak = vars[4]
            self.vpnusers = int(vals)
            #print ("Current Remote Users: ",vals)
            #print ("Peak number of users:", peak)
            self.set_message("VPN Users: {}".format(vals))
            self.add_perfdata("'VPN_Users'= {}".format(vals))

        net_connect.disconnect()

    def add_status(self, status):
        """ Set the status only if it is more severe than the present status
        The order of severity being OK, WARNING, CRITICAL, UNKNOWN
        :param status: Status to set, one of the self.STATUS_xxx constants
        :return: The current status
        """
        if self.status is None or status > self.status:
            self.status = status

    def set_message(self, message):
        self.messages = [message]

    def add_message(self, message):
        self.messages.append(message)

    def add_perfdata(self, perfitem):
        self.perfdata.append(perfitem)

    def compare_users(self):
        if self.vpnusers < self.options.warning:
            self.status = self.STATUS_OK
        elif self.vpnusers < self.options.critical:
            self.status = self.STATUS_WARNING
        else:
            self.status = self.STATUS_CRITICAL

if __name__ == "__main__":
    checker = VpnUserChecker()
    result = checker.run()
    exit(result)
