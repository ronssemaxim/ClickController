"""
SSH.py. Creates and maintains an SSH connection

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import paramiko as paramiko
import Logger

from Kube.Config import MASTER_NODE_NAME, NODES
from MainConfig import DO_LOG_SSH_CMDS_TO_FILE, LOG_SSH_FILE

# used to cache an often used SSH connection
master_ssh_con = None


def get_ssh_con_master(cached=True):
    """
    Gets a reference to an ssh connection with the master node
    :param cached:
    :return:
    """
    # in case caching is not desired at all:
    # return SSH(MASTER_NODE_NAME, nodes[MASTER_NODE_NAME]["username"],
    #                             nodes[MASTER_NODE_NAME]["password"])  # connect to master
    global master_ssh_con
    # if caching is allowed, check if connection already exists or create new one
    if cached:
        if master_ssh_con is None:
            master_ssh_con = SSH(MASTER_NODE_NAME, NODES[MASTER_NODE_NAME]["username"],
                                 NODES[MASTER_NODE_NAME]["password"])  # connect to master
        return master_ssh_con
    else:
        # if not cached ==> return new connection
        return SSH(MASTER_NODE_NAME, NODES[MASTER_NODE_NAME]["username"], NODES[MASTER_NODE_NAME]["password"])


class SSH:
    stdout = None
    stdin = None
    stderr = None
    host = None

    def __init__(self, host, username, password, strict=False):
        """
        Initializes an SSH object and connects to the host
        :param host: hostname or IP
        :param username: username
        :param password: password
        :param strict: set to True to check server public key against the known_hosts file, or False to disable
        """
        self.host = host
        Logger.log("SSH", "Connecting to " + host + ", username = " + username, 10)
        self.con = paramiko.SSHClient()
        if not strict:
            self.con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        Logger.log("SSH", "connection setup", 6)
        self.con.connect(host, username=username, password=password)

    def exec(self, cmd, asArray=False, mayFail=False, mustReturnOutput=False):
        """
        Executes an SSH command and returns both stdout and stderr lines combined
        :param cmd: command to execute
        :param asArray: return the output lines as a list or as one blob of text.
        :param mayFail: if True, prints an error message to the screen (verbose level 2 or higher) if the command
        produces an error string
        :param mustReturnOutput: if the command returns empty output on both stderr & stdout, execute the command again
        :return: the output (list or string). Note: if as array, the end of each
        line might contain a newline character
        """
        Logger.log("SSH", "Executing command \"" + cmd + "\" on host " + self.host, 10)
        if DO_LOG_SSH_CMDS_TO_FILE:
            Logger.write_to_file(LOG_SSH_FILE, "", cmd, 0)

        self.stdin, self.stdout, self.stderr = self.con.exec_command(cmd)
        err_lines = self.stderr.readlines()
        if len(err_lines) > 0 and not mayFail:
            Logger.log("SSH", "SSH ERROR: " + ''.join(err_lines), 2)

        lines = self.stdout.readlines() + err_lines
        # if must return output: check if lines list is empty, and execute again
        if mustReturnOutput and len(lines) <= 0:
            if len(lines) <= 0:
                Logger.log("SSH", "Command " + cmd + " returned nothing, trying again", 7)
            return self.exec(cmd, asArray, mayFail, mustReturnOutput)

        return lines if asArray else ''.join(lines)

    def run(self, cmd, asArray=False, mayFail=False, mustReturnOutput=False):
        """
        Alias for exec()
        :param cmd:
        :param asArray:
        :param mayFail:
        :param mustReturnOutput:
        :return:
        """
        return self.exec(cmd, asArray, mayFail, mustReturnOutput)

    def __exit__(self, exc_type, exc_value, traceback):
        # destructor
        self.con.close()
