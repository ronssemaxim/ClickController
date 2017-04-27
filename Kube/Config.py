"""
Kube/Config.py. Used to configure Kubernetes options.

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""

from MainConfig import ClickComponentName
from PrivateConfig import PRIVATE_NODES, privateMasterNode

# dictionary of kubernetes nodes {hostname: {
#  {"ip":str, "username":str, "password":str, "healthPort":int, "apiPort":int, "maxUplinkSpeed":bps
# }, ... }
NODES = PRIVATE_NODES

# hostname of the master node
MASTER_NODE_NAME = privateMasterNode

# the component label for the deployments and their value per component type
# format for the value: [a-zA-Z0-9]+
KUBE_COMPONENT_TO_LABEL_VALUE = {
    ClickComponentName.IPSecEnc: "ipsecenc",
    ClickComponentName.IPSecDec: "ipsecdecr",
    ClickComponentName.QoS: "qos",
    ClickComponentName.Firewall: "firewall",
    ClickComponentName.TrafficShaper: "shaper"
}

# inverse of KUBE_COMPONENT_TO_LABEL_VALUE (for easy access, don't change this)
KUBE_LABEL_VALUE_TO_COMPONENT = {v: k for k, v in KUBE_COMPONENT_TO_LABEL_VALUE.items()}
