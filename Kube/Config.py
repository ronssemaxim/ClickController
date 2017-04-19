"""
Kube/Config.py. Used to configure Kubernetes options.

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""

# dictionary of kubernetes nodes hostname: {
#  {ip:, username:, password:, healthPort:, apiPort:, maxUplinkSpeed:
# }
from PyClickController.MainConfig import ClickComponentName

NODES = {
    "kubenode1.vpnmaxim.wall2-ilabt-iminds-be.wall2.ilabt.iminds.be": {
        "ip": "193.190.127.210",
        "username": "click-controller",
        "password": "Azerty123",
        "healthPort": 10255,
        "apiPort": 6443,
        "maxUplinkSpeed": 1024*1024  # in bps
    }
}
# hostname of the master node
MASTER_NODE_NAME = "kubenode1.vpnmaxim.wall2-ilabt-iminds-be.wall2.ilabt.iminds.be"

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
