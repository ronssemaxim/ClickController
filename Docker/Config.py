"""
Docker/Config.py. Used to configure options for docker

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""

# the image names for each component. Image names need not to be unique
from MainConfig import ClickComponentName

IMAGE_NAMES = {
    ClickComponentName.IPSec: "ronssemaxim/click-crypto",
    ClickComponentName.QoS: "ronssemaxim/click-qos",
    ClickComponentName.Firewall: "ronssemaxim/click-firewall",
    ClickComponentName.TrafficShaper: "ronssemaxim/click-shaper",
}
