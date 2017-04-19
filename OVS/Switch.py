"""
OVS/Switch.py. Manages an Open vSwitch

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import re

import Logger
from OVS.Config import OVS_SWITCH_NAME
from SSH import get_ssh_con_master


def get_dpdkr_to_ovs_nr():
    """
    Get the DPDKR port number to the OpenFlow port number from the switch
    :return: dictionary {dpdkr:ovs,...}
    """
    # lines always are in the form " 123(dpdkr12)...."
    pattern = re.compile("\s(\d+)\(dpdkr(\d+)\)")
    ret_dict = {}
    for line in get_ssh_con_master().exec("sudo ovs-ofctl show " + OVS_SWITCH_NAME, asArray=True, mayFail=False):
        match = pattern.match(line)
        if match:
            ret_dict[int(match.groups()[1])] = int(match.groups()[0])
    return ret_dict


def get_ovs_to_dpdkr_nr():
    """
    Get the OpenFlow port number to DPDKR number mapping from the switch
    :return: dictionary {ovs:dpdkr,...}
    """
    # lines always are in the form " 123(dpdkr12)...."
    pattern = re.compile("\s(\d+)\(dpdkr(\d+)\)")
    ret_dict = {}
    for line in get_ssh_con_master().exec("sudo ovs-ofctl show " + OVS_SWITCH_NAME, asArray=True, mayFail=False):
        match = pattern.match(line)
        if match:
            ret_dict[match.groups()[0]] = int(match.groups()[1])
    return ret_dict


def get_dpdk_to_ovs_nr():
    """
    Get the DPDK port number to the OpenFlow port number from the switch
    :return: dictionary {dpdk:ovs,...}
    """
    # lines always are in the form " 123(dpdk12)...."
    pattern = re.compile("\s(\d+)\(dpdk(\d+)\)")
    ret_dict = {}
    for line in get_ssh_con_master().exec("sudo ovs-ofctl show " + OVS_SWITCH_NAME, asArray=True, mayFail=False):
        match = pattern.match(line)
        if match:
            ret_dict[int(match.groups()[1])] = int(match.groups()[0])
    return ret_dict


def get_ovs_to_dpdk_nr():
    """
    Get the OpenFlow port number to DPDK number mapping from the switch
    :return: dictionary {ovs:dpdk,...}
    """
    # lines always are in the form " 123(dpdk12)...."
    pattern = re.compile("\s(\d+)\(dpdk(\d+)\)")
    ret_dict = {}
    for line in get_ssh_con_master().exec("sudo ovs-ofctl show " + OVS_SWITCH_NAME, asArray=True, mayFail=False):
        match = pattern.match(line)
        if match:
            ret_dict[match.groups()[0]] = int(match.groups()[1])
    return ret_dict


def get_ovs_port_rxtx():
    """
    Get amount of rx/tx bytes/pkts/drop/errs per OpenFlow port
    Note: DPDK Rings always have "0" as byte count, so packet count must be used
    :return: dictionary {ovsPortNr: {"rx": {"pkts":,"drop":,"errs":}, "tx": {"pkts":,"drop":,"errs":}} }
    """
    # Form: "  port 123: rx pkts=1234, bytes=1234, drop=1234, errs=1234, ..."
    patternRx = re.compile("\s*port\s+(\d+): rx pkts=(\d+),.*?, drop=(\d+), errs=(\d+)")
    # Form: "            tx pkts=1234, bytes=1234, drop=1234, errs=1234, ..."
    patternTx = re.compile("\s*tx pkts=(\d+),.*?, drop=(\d+), errs=(\d+)")
    ret_dict = {}
    # sometimes this command fails, so keep executing it untill it succeeds.
    lines = get_ssh_con_master().exec("sudo ovs-ofctl dump-ports " + OVS_SWITCH_NAME, asArray=True, mayFail=False,
                                      mustReturnOutput=True)
    Logger.log("Switch", "In get_ovs_port_rx_tx, lines = " + str(lines), 9)
    # loop over ssh output, match regex
    for i in range(0, len(lines)):
        matchRx = patternRx.match(lines[i])
        if matchRx:
            matchTx = patternTx.match(lines[i+1])
            ret_dict[int(matchRx.groups()[0])] = {
                "rx": {
                    "pkts": int(matchRx.groups()[1]),
                    "drop": int(matchRx.groups()[2]),
                    "errs": int(matchRx.groups()[3])
                },
                "tx": {
                    "pkts": int(matchTx.groups()[0]),
                    "drop": int(matchTx.groups()[1]),
                    "errs": int(matchTx.groups()[2])
                }
            }
    return ret_dict

'''
def delete_switch():
    get_ssh_con_master().exec("sudo ovs-vsctl del-br " + OVS_SWITCH_NAME, mayFail=True)


def create_switch():
    con = get_ssh_con_master()
    con.exec("sudo ovs-vsctl add-br br0 -- set bridge " + OVS_SWITCH_NAME + " datapath_type=netdev")
    # dpdk0 has always OVS port number 1
    con.exec("sudo ovs-vsctl add-port " + OVS_SWITCH_NAME + " dpdk0 -- set Interface dpdk0 type=dpdk options:tx-flow-
    ctrl=on")

def recreate_switch():
    delete_switch()
    create_switch()


def create_ring(nr):
    get_ssh_con_master().exec(
        "sudo ovs-vsctl add-port " + OVS_SWITCH_NAME + " dpdkr" + str(nr) + " -- set Interface dpdkr" + str(
            nr) + " type=dpdkr")


def del_ring(nr):
    get_ssh_con_master().exec("sudo ovs-vsctl del-port " + OVS_SWITCH_NAME + " dpdkr" + str(nr))
'''
