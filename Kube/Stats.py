"""
Kube/Stats.py. Used to fetch statistics from k8s

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import re
from datetime import datetime
from time import time

import requests

import Logger
from Kube.Config import NODES
from MainConfig import CORE_COUNT_PER_CONTAINER, KUBE_DEPLOYMENT_PREFIX
from OVS.Switch import get_ovs_port_rxtx

# fetch initial network usage per ovs port
last_network_usage = get_ovs_port_rxtx()
last_network_usage_fetched = time()  # num of seconds since epoch


def kube_datetime_to_python_datetime(str_datetime):
    """
    Converts a Kubernetes datetime object to a python datetime object
    :param str_datetime: string representation of the kubernetes datetime
    :return: python formatted string
    """
    str_datetime = str_datetime[:-9]  # remove last 8 chars
    return datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%f')


def get_load_per_pod(node_name, dpdkr_to_ovs_nr):
    """
    Get the load for each pod on a specific node
    :param node_name: hostname/DNSname of the node
    :param dpdkr_to_ovs_nr: a mapping of DPDK ring numbers to OVS number
    :return: a dictionary with a mapping podName: { "cpu":,"network":,}
    """
    node = NODES[node_name]
    ret_dict = {}

    try:
        # fetch pod load from healthz handler
        r = requests.get("http://" + node_name + ":" + str(node["healthPort"]) + "/stats/summary")
        # pods->podRef->name
        # kubeDeploymentPrefix
        # pods->containers->cpu->usageCoreNanoSeconds  / (coreCountPerContainer * 1e+9)
        if r.status_code == 200:
            json = r.json()
            Logger.log("Stats", "Node " + node_name + " is up", 2)
            Logger.log("json", json)

            current_network_usage = get_ovs_port_rxtx()

            pop_ports = []
            # fetch network usage first, aggregate with node stats
            # subtract last_network_usage from current_network_usage
            for port, data in last_network_usage.items():
                # if port still exists
                if port in current_network_usage:
                    relRx = current_network_usage[port]["rx"]["pkts"] - last_network_usage[port]["rx"]["pkts"]
                    relTx = current_network_usage[port]["tx"]["pkts"] - last_network_usage[port]["tx"]["pkts"]
                    last_network_usage[port]["max"] = max(relRx, relTx)
                    relRx = current_network_usage[port]["rx"]["drop"] - last_network_usage[port]["rx"]["drop"]
                    relTx = current_network_usage[port]["tx"]["drop"] - last_network_usage[port]["tx"]["drop"]
                    last_network_usage[port]["drops"] = max(relRx, relTx)
                    relRx = current_network_usage[port]["rx"]["errs"] - last_network_usage[port]["rx"]["errs"]
                    relTx = current_network_usage[port]["tx"]["errs"] - last_network_usage[port]["tx"]["errs"]
                    last_network_usage[port]["errs"] = max(relRx, relTx)
                    # copy current to last network stats
                    last_network_usage[port]["rx"] = current_network_usage[port]["rx"]
                    last_network_usage[port]["tx"] = current_network_usage[port]["tx"]
                # else remove port from stats
                else:
                    Logger.log("Stats", "OVS port nr " + str(port) + " deleted from host, "
                                                                     "removing from dictionary aswel." +
                                                                     str(current_network_usage), 2)
                    pop_ports.append(port)  # add to pop_ports (DONT delete it here
                    # , else: dictionary changed size during iteration
            # delete here
            for port in pop_ports:
                last_network_usage.pop(port, None)

            pattern = re.compile(KUBE_DEPLOYMENT_PREFIX + "-[a-zA-Z0-9]+-(\d+)-")
            for pod in json["pods"]:
                podName = pod["podRef"]["name"]
                match = pattern.match(podName)
                if match:
                    dpdkr_nr = int(match.groups()[0])
                    Logger.log("Stats", "Found pod with name " + podName, 7)
                    # if pod is being created or destroyed, containers or it's stats will be empty
                    if pod["containers"] and "cpu" in pod["containers"][0]:
                        cpuUsage = int(pod["containers"][0]["cpu"]["usageCoreNanoSeconds"]) / \
                                   (CORE_COUNT_PER_CONTAINER * 1e+9)
                        Logger.log("Stats", "Network usage = " + str(last_network_usage), 9)
                        networkUsage = last_network_usage[dpdkr_to_ovs_nr[dpdkr_nr]]["max"]
                        ret_dict[podName] = {
                            "cpu": cpuUsage,
                            "network": networkUsage
                        }
                    else:
                        Logger.log("Stats", "Pod " + podName + " has no containers (probably exiting/starting)", 7)
        else:
            Logger.log("Stats", "Node " + node_name + " is down", 2)
    except (requests.exceptions.HTTPError, ValueError) as exc:
        Logger.log("Stats", "Error => Node " + node_name + " is partially down, error details: ", 1)
        Logger.log("Stats", exc, 1)
    except requests.exceptions.ConnectionError as exc:
        Logger.log("Stats", "Error => Node " + node_name + " is down, error details: ", 1)
        Logger.log("Stats", exc, 1)

# returns pointer
    return ret_dict
