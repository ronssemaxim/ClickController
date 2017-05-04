"""
OVS/Config.py. Used to configure Open vSwitch options.

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
from MainConfig import ClickComponentName

# mapping of click component to multipath options.
# {ClickComponentName: {"beforeTable":x,"afterTable":y,"register":z}, ...}
KUBE_COMPONENT_TO_OVS_CONFIG = {
    ClickComponentName.IPSec: {
        "beforeTable": "2",
        "afterTable": "3",
        "register": "0"
    },
    ClickComponentName.QoS: {
        "beforeTable": "4",
        "afterTable": "5",
        "register": "1"
    },
    ClickComponentName.Firewall: {
        "beforeTable": "6",
        "afterTable": "7",
        "register": "2"
    },
    ClickComponentName.TrafficShaper: {
        "beforeTable": "8",
        "afterTable": "9",
        "register": "3"
    }
}

# name of the existing Open vSwitch
OVS_SWITCH_NAME = "br0"
