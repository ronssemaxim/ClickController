"""
MainConfig.py. Main config file which contains the parameters specific for the ClickController

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
from enum import Enum

VERBOSE = 11  # verbose level. Lower is less output and vice versa
DO_LOG_TO_FILE = False  # logs output sent to the screen also to a log file
DO_LOG_SSH_CMDS_TO_FILE = False  # logs all SSH commands to a file, not their output
DO_LOG_JSON_TO_FILE = False  # WARNING!!! This can fill your disk pretty fast! Approximately 70MB / 2h
LOG_FILE = "/Users/maximronsse/Downloads/click-controller-log.txt"
LOG_SSH_FILE = "/Users/maximronsse/Downloads/click-controller-ssh-cmds-log.txt"
LOG_JSON_FILE = "/Users/maximronsse/Downloads/click-controller-json-log.txt"
DO_INIT_DEPLOYMENTS = True  # Set to false to disable deployment deletion and recreation at startup of the main script
HISTORY_LENGTH = 60  # in minutes
UPDATE_INTERVAL = 1  # delay, in seconds, between two consecutive checks if deployments are under or overloaded

INTERNAL_DPDK_NR = 1  # DPDK port number (numeric) for the internal interface, being the interface where the company's
# internal network is
EXTERNAL_DPDKR_NR = 0  # DPDK port number (numeric) for the external interface, being the interface which connects
# to the ISP
INCOMING_VLAN = 10
OUTGOING_VLAN = 11

CORE_COUNT_PER_CONTAINER = 24  # number of cores one container is assigned
DELETE_DEPLOYMENT_AFTER = 2  # wait for this amount of seconds after the OpenFlow rules have been delete before deleting
# the deployment
DEPLOYMENT_READY_TIME = 70  # wait for this amount of seconds after the instance was started before adding the OpenFlow
# rules

KUBE_DEPLOYMENT_PREFIX = "component"  # the prefix for the name of the kubernetes deployments
KUBE_COMPONENT_LABEL_NAME = "clickcomponent"  # name of the label used to identify the Click component
KUBE_DPDK_RING_LABEL_NAME = "dpdkr"  # name of the label used to specify the DPDK Ring number

NETWORK_SATURATED_AT = 80  # in percent
NETWORK_DESATURATED_AT = 30  # lower trigger, in percent
CPU_OVERLOADED_AT = 80  # in percent
CPU_UNDERLOADED_AT = 35  # lower trigger, in percent


# definition of Click Components
class ClickComponentName(Enum):
    """
    An enum used to define the VPN Component types and their internal number (never used)
    """
    IPSecEnc = 1
    IPSecDec = 2
    Firewall = 3
    QoS = 4
    TrafficShaper = 5
    Test = 6

# maximum number of packets per second one container instance for a specific component can process
MAX_NETWORK_PKTS_PER_COMPONENT = {
    ClickComponentName.IPSecEnc: 5,
    ClickComponentName.IPSecDec: 5,
    ClickComponentName.QoS: 10,
    ClickComponentName.Firewall: 10,
    ClickComponentName.TrafficShaper: 10
}

# processing order of the VPN components
# VPN net -> shaper -> qos -> decrypt -> firewall -> internal net
VPN_COMPONENTS_ORDER_INCOMING = [
    ClickComponentName.TrafficShaper,
    ClickComponentName.QoS,
    ClickComponentName.IPSecDec,
    ClickComponentName.Firewall,
]
# internal net -> shaper -> firewall -> qos -> encrypt -> VPN net
VPN_COMPONENTS_ORDER_OUTGOING = [
    ClickComponentName.TrafficShaper,
    ClickComponentName.Firewall,
    ClickComponentName.QoS,
    ClickComponentName.IPSecEnc,
]
