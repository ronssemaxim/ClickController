"""
main.py. Main script for the controller. Steps it takes:
1: delete old Kubernetes (k8s) deployments and all OpenFlow rules
2: create new deployments, configure OpenFlow rules
3: monitor deployments, start/stop a deployment if load is not appropriate

To setup the ClickController properly, first configure the nodes and the master_node_name in Kube/Config.py

Next define MainConfig.py:ClickComponentName. After this has been defined, set the MAX_NETWORK_PKTS_PER_COMPONENT,
VPN_COMPONENTS_ORDER_INCOMING, VPN_COMPONENTS_ORDER_OUTGOING, Docker/Config.py:IMAGE_NAMES,
OVS/Config.py:KUBE_COMPONENT_TO_OVS_CONFIG, Kube/Config.py:KUBE_COMPONENT_TO_LABEL_VALUE

If the host was not prepared using the provided preparation host, you might also needs to be changed
(OVS/Config.py:ovs_switch_name)

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import re
import time

import math

from PyClickController import Logger
from PyClickController.Initialize import create_initial_deployments, create_deployment_for_component
from PyClickController.Kube.Config import MASTER_NODE_NAME, KUBE_LABEL_VALUE_TO_COMPONENT, KUBE_COMPONENT_TO_LABEL_VALUE
from PyClickController.Kube.Deployment import delete_deployment_delayed
from PyClickController.Kube.Stats import get_load_per_pod
from PyClickController.MainConfig import UPDATE_INTERVAL, VPN_COMPONENTS_ORDER_INCOMING, \
    VPN_COMPONENTS_ORDER_OUTGOING, CPU_OVERLOADED_AT, CPU_UNDERLOADED_AT, KUBE_DEPLOYMENT_PREFIX, \
    NETWORK_SATURATED_AT, NETWORK_DESATURATED_AT, DELETE_DEPLOYMENT_AFTER, DEPLOYMENT_READY_TIME, \
    MAX_NETWORK_PKTS_PER_COMPONENT
from PyClickController.OVS.Config import KUBE_COMPONENT_TO_OVS_CONFIG
from PyClickController.OVS.Flow import delete_flow, get_multipath_rule, add_flow, add_flows_for_new_deployment_delayed
from PyClickController.OVS.Switch import get_dpdk_to_ovs_nr, get_dpdkr_to_ovs_nr, get_ovs_to_dpdkr_nr

########################################################################################################################
#   0: Script Initialisation

Logger.log("XXX", "Starting Click Controller, v0.9")
dpdk_to_ovs_port_nr = get_dpdk_to_ovs_nr()
ovs_to_dpdkr_nr = get_ovs_to_dpdkr_nr()
dpdkr_to_ovs_nr = get_dpdkr_to_ovs_nr()

# when a certain component type got a deployment added or deleted
last_deployment_added_or_deleted = {}
for component_type in KUBE_COMPONENT_TO_LABEL_VALUE:
    last_deployment_added_or_deleted[component_type] = 0

history = {}

# create initial ssh connections
# sshCons = {}
# for (name, node) in nodes.items():
#     ssh = SSH(name, node["username"], node["password"])
#     Logger.log("ssh", "Date on " + name + ": " + ssh.exec("date"), 1)
#     sshCons[name] = ssh

Logger.log("XXX", "Scrip initialisation done", 1)

########################################################################################################################
#   1: Cluster Initialisation

Logger.log("XXX", "Starting cluster initialisation", 1)
# STEP 1: deploy initial pods
Logger.log("XXX", "Creating initial deployments and searching for existing deployments", 2)
deployments_per_component = create_initial_deployments(dpdkr_to_ovs_nr)
Logger.log("XXX", "Deployments per container: " + str(deployments_per_component), 7)

Logger.log("XXX", "Cluster initialisation done", 1)


########################################################################################################################
#   infinite loop (step 3)


# keep running this loop
while True:
    # get load for each pod from the K8s API
    load_per_pod = get_load_per_pod(MASTER_NODE_NAME, dpdkr_to_ovs_nr)
    load_per_component = {}
    # initialize load for each component
    for component_type in KUBE_COMPONENT_TO_LABEL_VALUE:
        load_per_component[component_type] = {
            "cpu": 0,
            "network": 0
        }

    # keep track of unique deployment names, since "Terminating" deployments might still return, resulting in a
    # duplicate
    discovered_deployments = {}
    # loop over improperly loaded pods, aggregate results for this component
    for (podName, load) in load_per_pod.items():
        pattern = re.compile("(" + KUBE_DEPLOYMENT_PREFIX + "-([a-zA-Z0-9]+)-\d+)-")
        match = pattern.match(podName)
        if match:
            deployment_name = match.groups()[0]
            if deployment_name not in discovered_deployments:
                component_name = match.groups()[1]
                component_type = KUBE_LABEL_VALUE_TO_COMPONENT[component_name]
                load_per_component[component_type]["cpu"] += load["cpu"]  # aggregate here
                load_per_component[component_type]["network"] += load["network"]
                discovered_deployments[deployment_name] = True
                Logger.log("XXX", "Deployment " + deployment_name + " is of component name " + component_name +
                           ", which is of type " + str(component_type) + ", so load of this component is now: " +
                           str(load_per_component[component_type]), 9)

    # at this point, all deployments have been processed and the load has been aggregated per component type
    # next step: average load for each component
    Logger.log("XXX", "Load per component: " + str(load_per_component), 7)
    Logger.log("XXX", "Load per pod: " + str(load_per_pod), 7)
    Logger.log("XXX", "Deployments per component: " + str(deployments_per_component), 7)
    # loop over all components, find the ones who are over/under loaded
    for component_type, lbl_value in KUBE_COMPONENT_TO_LABEL_VALUE.items():
        dep_count = len(deployments_per_component[component_type])
        if dep_count > 0:
            cpuUsage = load_per_component[component_type]["cpu"] / \
                       dep_count
            networkUsage = load_per_component[component_type]["network"] / \
                           (MAX_NETWORK_PKTS_PER_COMPONENT[component_type] / 100)
        else:
            continue  # this component might not have any deployments (eg if it is never used in any chain)

        # check if the component recently got a deployment removed or added ==> wait for the container to start and be
        # hot, or wait for it to be deleted
        seconds_since_last_deployment = time.time() - last_deployment_added_or_deleted[component_type]
        if seconds_since_last_deployment <= max(DEPLOYMENT_READY_TIME, DELETE_DEPLOYMENT_AFTER) + 5:
            Logger.log("XXX", "Component " + str(component_type) + " got a deployment added or removed " +
                       str(math.floor(seconds_since_last_deployment)) + " seconds ago ==> skipping", 2)
            continue

        Logger.log("XXX", "Component " + str(component_type) + " has " + str(cpuUsage) + "% cpu usage and " +
                   str(networkUsage) + "% network usage", 5)

        if cpuUsage > CPU_OVERLOADED_AT or networkUsage > NETWORK_SATURATED_AT:  # overloaded ==> start new pod
            Logger.log("XXX", "Overloaded component " + str(component_type) + " (" + str(cpuUsage) + "%/" +
                       str(CPU_OVERLOADED_AT) + "% cpu usage and " + str(networkUsage) + "pkts/sec / " +
                       str(NETWORK_SATURATED_AT) + "pkts/sec) has " + str(dep_count) + " deployments, adding new deployment ", 1)

            try:
                # first: create new deployment for this component
                deployment = create_deployment_for_component(component_type, dpdkr_to_ovs_nr)
                next_dpdkr = deployment["dpdkr"]
                deployment_name = deployment["name"]
                deployments_per_component[component_type].append({
                    "name": deployment_name,
                    "dpdkr": next_dpdkr,
                    "ovsPort": dpdkr_to_ovs_nr[next_dpdkr],  # get actual OVS number of port (!= dpdk nr)
                    "type": component_type
                })

                # then: wait for the container to start (become hot) and then create the flows to this container
                add_flows_for_new_deployment_delayed(deployments_per_component, component_type, dpdk_to_ovs_port_nr)

                last_deployment_added_or_deleted[component_type] = time.time()
            except IndexError:
                Logger.log("XXX", "ERROR! No free dpdkr port found! "
                                  "Add new dpdkr ports, or reduce number of components")

        # underloaded ==> check if #deployments for this component > 1
        if cpuUsage < CPU_UNDERLOADED_AT or networkUsage < NETWORK_DESATURATED_AT:
            if dep_count > 1:  # has more than one deployment ==> remove last started one
                if len(deployments_per_component[component_type]) <= 0:
                    Logger.log("XXX", "ErrorInfo: Load for this component: " + str(load_per_component[component_type]))
                    Logger.log("XXX", "ErrorInfo: Deployments for this component: " + str(deployments_per_component[component_type]))
                    Logger.log("XXX", "ErrorInfo: Load for this component: " + str(load_per_component[component_type]))
                    Logger.log("XXX", "ErrorInfo: Load for each pod: " + str(load_per_pod))
                    raise KeyError("At least one deployment of each component should be available at this point, but " +
                                   str(component_type) + " has " + str(len(deployments_per_component[component_type])))

                Logger.log("XXX", "Underloaded component " + str(component_type) + " (" + str(cpuUsage) + "%/" +
                       str(CPU_OVERLOADED_AT) + "% cpu usage and " + str(networkUsage) + "pkts/sec / " +
                       str(NETWORK_SATURATED_AT) + "pkts/sec) has " +
                           str(dep_count) +
                           " deployments, removing last added deployment " +
                           deployments_per_component[component_type][-1]["name"], 1)
                # add new multipath rule with one less output for each chain (in & outgoing chain)
                rule = get_multipath_rule(VPN_COMPONENTS_ORDER_INCOMING, component_type,
                                          dep_count - 1,
                                          True, dpdk_to_ovs_port_nr)
                if rule:  # rule might not exist, eg incoming chain has no encryption component
                    add_flow(rule)

                rule = get_multipath_rule(VPN_COMPONENTS_ORDER_OUTGOING, component_type,
                                          dep_count - 1,
                                          False, dpdk_to_ovs_port_nr)
                if rule:
                    add_flow(rule)

                # remove flows going to and coming from the dpdkr ring
                delete_flow("\"reg" + str(KUBE_COMPONENT_TO_OVS_CONFIG[component_type]["register"]) + "=" +
                            str(dep_count-1) + "\"")
                delete_flow("\"in_port=" + str(deployments_per_component[component_type][-1]["ovsPort"]) + "\"")

                # delete actual deployment
                delete_deployment_delayed(deployments_per_component[component_type][-1])

                # update local variables
                deployments_per_component[component_type].pop()  # remove last deployment from this component
                last_deployment_added_or_deleted[component_type] = time.time()
            else:
                Logger.log("XXX", "Underloaded component " + str(component_type) + " has " +
                           str(dep_count) +
                           " deployments, so not enough to remove the last added deployment " +
                           deployments_per_component[component_type][-1]["name"], 6)

    time.sleep(UPDATE_INTERVAL)

Logger.log("XXX", "done!")
