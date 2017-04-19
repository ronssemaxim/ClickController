"""
OVS/Config.py. Used to configure Open vSwitch options.

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
from PyClickController.MainConfig import ClickComponentName

# mapping of click component to multipath options.
# {ClickComponentName: {"beforeTable":x,"afterTable":y,"register":z}, ...}
KUBE_COMPONENT_TO_OVS_CONFIG = {
    ClickComponentName.IPSecEnc: {
        "beforeTable": "2",
        "afterTable": "3",
        "register": "0"
    },
    ClickComponentName.IPSecDec: {
        "beforeTable": "4",
        "afterTable": "5",
        "register": "1"
    },
    ClickComponentName.QoS: {
        "beforeTable": "6",
        "afterTable": "7",
        "register": "2"
    },
    ClickComponentName.Firewall: {
        "beforeTable": "8",
        "afterTable": "9",
        "register": "3"
    },
    ClickComponentName.TrafficShaper: {
        "beforeTable": "10",
        "afterTable": "11",
        "register": "4"
    }
}

# name of the existing Open vSwitch
OVS_SWITCH_NAME = "br0"
