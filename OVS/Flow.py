"""
OVS/Flow.py. Manages the flows for an Open vSwitch

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import Logger
from DelayedInvoke import DelayedInvoke
from MainConfig import VPN_COMPONENTS_ORDER_INCOMING, VPN_COMPONENTS_ORDER_OUTGOING, \
    EXTERNAL_DPDKR_NR, INTERNAL_DPDK_NR, DEPLOYMENT_READY_TIME
from OVS.Config import OVS_SWITCH_NAME, KUBE_COMPONENT_TO_OVS_CONFIG
from OVS.Switch import get_dpdk_to_ovs_nr
from SSH import get_ssh_con_master


def delete_all_flows():
    """
    Deletes all flows from the OVS switch
    """
    get_ssh_con_master().exec("sudo ovs-ofctl del-flows " + OVS_SWITCH_NAME, mayFail=True)


def add_flow(flow, use_cache_ssh_con=True):
    """
    Add a flow
    :param flow: OpenFlow string
    :param use_cache_ssh_con: whether or not to use a cached SSH connection (set to False when used in a thread)
    """
    get_ssh_con_master(cached=use_cache_ssh_con).exec("sudo ovs-ofctl add-flow " + OVS_SWITCH_NAME + " " + flow,
                                                      mayFail=False)


def delete_flow(flow):
    """
    Delete a flow
    :param flow: OpenFlow string
    """
    get_ssh_con_master().exec("sudo ovs-ofctl del-flows " + OVS_SWITCH_NAME + " " + flow, mayFail=False)


def get_multipath_rule(chain, component_type, modulo, is_incoming, dpdk_to_ovs_nr):
    """
    Get the multipath OpenFlow rule for a certain component.
    :param chain: The complete chain where the component resides in. Needed to know the previous component and to
    connect them to eachother
    :param component_type: the type of the component to generate the rule for. Needed to know the position of this
    component in the chain
    :param modulo: how many instances run inside this component. The hash will be calculated%module.
    :param is_incoming: whether this is an incoming or outgoing chain
    :param dpdk_to_ovs_nr: the dpdk port number to ovs port number (used for in_port=...)
    :return: the unexecuted OpenFlow rule
    """

    # check if this component is used in this chain (eg Encr & Decr)
    if component_type not in chain:
        return
    # if first component ==> add "in_port="
    #       else ==> add "table="
    chain_nr = chain.index(component_type)
    if chain_nr == 0:
        push_vlan = "mod_vlan_vid:"
        push_vlan += "10" if is_incoming else "11"
        push_vlan += ","
        in_port = str(dpdk_to_ovs_nr[EXTERNAL_DPDKR_NR if is_incoming else INTERNAL_DPDK_NR])
        ret = "\"in_port=" + in_port + ",actions=" + push_vlan + ","
    else:
        check_vlan = "dl_vlan="
        check_vlan += "10" if is_incoming else "11"
        check_vlan += ","
        ret = "\"table=" + str(KUBE_COMPONENT_TO_OVS_CONFIG[chain[chain_nr - 1]]["afterTable"]) + \
              "," + check_vlan + "actions="
    ret += "multipath(symmetric_l3l4+udp, " \
        "1024, " \
        "modulo_n, " + str(modulo) + "," \
        " 0, " \
        "NXM_NX_REG" + str(KUBE_COMPONENT_TO_OVS_CONFIG[component_type]["register"]) + "[0..31])," \
        "resubmit(," + str(KUBE_COMPONENT_TO_OVS_CONFIG[component_type]["beforeTable"]) + ")\""
    return ret


def create_chain_flows(chain, deployments_per_component, is_incoming):
    """
    Create all the flow rules for a single chain
    :param chain: List of component types. First element is the first component where the traffic enters, last component
    is the one where traffic exits
    :param deployments_per_component: list of deployments in a dictionary for each component
    :param is_incoming: whether this is an incoming or outgoing chain
    """
    ssh_con = get_ssh_con_master()
    dpdk_to_ovs_nr = get_dpdk_to_ovs_nr()

    out_port = str(dpdk_to_ovs_nr[INTERNAL_DPDK_NR if is_incoming else EXTERNAL_DPDKR_NR])

    # create flow from dpdk0 -> multipath first component -> before table from first component
    first_component = chain[0]
    Logger.log("Flow", "Creating flows for first component " + str(first_component), 4)

    ssh_con.exec("sudo ovs-ofctl add-flow " + OVS_SWITCH_NAME + " " +
                 get_multipath_rule(chain, first_component, 1, is_incoming, dpdk_to_ovs_nr))

    # before table from first component -> rings for this component
    ssh_con.exec("sudo ovs-ofctl add-flow " + OVS_SWITCH_NAME + " \""
                 "table=" + KUBE_COMPONENT_TO_OVS_CONFIG[first_component]["beforeTable"] + ","
                 "reg" + KUBE_COMPONENT_TO_OVS_CONFIG[first_component]["register"] + "=0,"
                 "actions=output:" + str(deployments_per_component[first_component][0]["ovsPort"]) + "\"")

    # from the rings -> to the after table
    # ovs-ofctl add-flow br0 "in_port=2,actions=resubmit(,3)"
    ssh_con.exec("sudo ovs-ofctl add-flow " + OVS_SWITCH_NAME + " \"in_port=" + str(
        deployments_per_component[first_component][0]["ovsPort"]) + ","
                                                                    "actions=resubmit(," +
                 KUBE_COMPONENT_TO_OVS_CONFIG[first_component]["afterTable"] + ")\"")

    prev_component = first_component
    for i in range(1, len(chain)):
        component = chain[i]
        Logger.log("Flow", "Creating flows for the next component " + str(component), 4)

        ssh_con.exec("sudo ovs-ofctl add-flow " + OVS_SWITCH_NAME + " " +
                     get_multipath_rule(chain, component, 1, is_incoming, dpdk_to_ovs_nr))

        # before table from component -> rings for this component
        ssh_con.exec("sudo ovs-ofctl add-flow " + OVS_SWITCH_NAME + " \""
                     "table=" + KUBE_COMPONENT_TO_OVS_CONFIG[component]["beforeTable"] + ","
                     "reg" + KUBE_COMPONENT_TO_OVS_CONFIG[component]["register"] + "=0,"
                     "actions=output:" + str(deployments_per_component[component][0]["ovsPort"]) + "\"")

        # from the rings -> to the after table
        # ovs-ofctl add-flow br0 "in_port=2,actions=resubmit(,3)"
        ssh_con.exec("sudo ovs-ofctl add-flow " + OVS_SWITCH_NAME + " \"in_port=" + str(
            deployments_per_component[component][0]["ovsPort"]) + ","
                                                                  "actions=resubmit(," +
                     KUBE_COMPONENT_TO_OVS_CONFIG[component]["afterTable"] + ")\"")

        prev_component = component

    check_vlan = "dl_vlan="
    check_vlan += "10" if is_incoming else "11"
    check_vlan += ","
    Logger.log("Flow", "Creating flow for last table to dpdk0 port", 4)
    ssh_con.exec("sudo ovs-ofctl add-flow " + OVS_SWITCH_NAME + " \""
                 "table=" + KUBE_COMPONENT_TO_OVS_CONFIG[prev_component]["afterTable"] + "," +
                 check_vlan +
                 "actions=output:" + out_port + ",strip_vlan\"")


def create_component_flows(deployments_per_component):
    """
    Create all the flow rules for both the in and outgoing chain.
    :param deployments_per_component: deployments_per_component: list of deployments in a dictionary for each component.
    Used to determine which DPDKR ring is used by which component/deployment
    """
    delete_all_flows()
    Logger.log("Flow", "Creating flows for incoming chain", 4)
    create_chain_flows(VPN_COMPONENTS_ORDER_INCOMING, deployments_per_component, True)
    Logger.log("Flow", "Creating flows for outgoing chain", 4)
    create_chain_flows(VPN_COMPONENTS_ORDER_OUTGOING, deployments_per_component, False)


def add_flows_for_new_deployment(deployments_per_component, component_type, dpdk_to_ovs_port_nr,
                                 use_cache_ssh_con=True):
    """
    Adds flows for a new deployment (flows only, not the Kube deployment itself)
    :param deployments_per_component: list of deployments in a dictionary for each component
    :param component_type: the type of component to add the flows for
    :param dpdk_to_ovs_port_nr: the dpdk port number to ovs port number (used for in_port=...)
    :param use_cache_ssh_con: whether or not to use a cached SSH connection (set to False when used in a thread)
    """
    dep_count = len(deployments_per_component[component_type])

    # create OpenFlow rules for this port (with the correct register)
    add_flow("\""
             "table=" + str(KUBE_COMPONENT_TO_OVS_CONFIG[component_type]["beforeTable"]) + ",reg" +
             str(KUBE_COMPONENT_TO_OVS_CONFIG[component_type]["register"]) + "=" +
             str(dep_count) + ","
                              "actions=output:" + str(deployments_per_component[component_type][-1]["ovsPort"]) + "\"",
             use_cache_ssh_con)
    add_flow("\"in_port=" + str(deployments_per_component[component_type][-1]["ovsPort"]) + ","
                                                                                            "actions=resubmit(," +
             str(KUBE_COMPONENT_TO_OVS_CONFIG[component_type]["afterTable"]) + ")\"", use_cache_ssh_con)

    # create Multipath rule
    rule = get_multipath_rule(VPN_COMPONENTS_ORDER_OUTGOING, component_type,
                              dep_count + 1,
                              False, dpdk_to_ovs_port_nr)
    if rule:
        add_flow(rule)


def add_flows_for_new_deployment_delayed(deployments_per_component, component_type, dpdk_to_ovs_port_nr):
    # calls add_flows_for_new_deployment_delayed after DEPLOYMENT_READY_TIME seconds, don't use cached SSH connection
    """

    :param deployments_per_component: list of deployments in a dictionary for each component
    :param component_type: the type of component to add the flows for
    :param dpdk_to_ovs_port_nr: the dpdk port number to ovs port number (used for in_port=...)
    :return:
    """
    thread = DelayedInvoke(add_flows_for_new_deployment, deployments_per_component, component_type, dpdk_to_ovs_port_nr,
                           False, exec_after=DEPLOYMENT_READY_TIME)
    thread.start()
    return thread
