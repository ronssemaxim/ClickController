"""
Docker/Config.py. Used to configure options for docker

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""

# the image names for each component. Image names need not to be unique
from PyClickController.MainConfig import ClickComponentName

IMAGE_NAMES = {
    ClickComponentName.IPSecEnc: "ronssemaxim/customclick",
    ClickComponentName.IPSecDec: "ronssemaxim/customclick",
    ClickComponentName.QoS: "ronssemaxim/customclick",
    ClickComponentName.Firewall: "ronssemaxim/customclick",
    ClickComponentName.TrafficShaper: "ronssemaxim/customclick",
}
