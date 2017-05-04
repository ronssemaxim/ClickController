ClickController
========================

A group of python scripts used to manage a Kubernetes cluster of containers running FastClick, connected to each 
other using Open vSwitch. This repository was made by Ronsse Maxim to support his master thesys.

How to setup
------------


To setup the host, execute the provided preparation script (developed under Ubuntu 16.04.1 LTS). Or follow the next
steps:
* install kubernetes(k8s) >=v1.5.0
* install Open vSwitch >=v2.5.0, with DPDK support (preferred higher due to various bug fixes)
* initialize the k8s master node, add the networking pods
* configure hugepages and enable DPDK support for Open vSwitch (OVS)
* restart the OVS daemon
* create an OVS switch (eg. br0) and add at least two DPDK ports to the switch (one for in and one for outgoing 
traffic)
* add dpdk ring ports to the new switch, the maximum number of ports is the maximum number of containers running
* create a new user with it's own group "click-controller", give sudo rights to execute ovs-* commands, set a 
password. Make sure the user has a shell and can connect to the master-node using SSH.
* copy /etc/kubernetes/admin.conf to Kube/kube-config.conf in this repository

To setup the ClickController properly, first set the NODES and the MASTER_NODE_NAME in Kube/Config.py

Next define MainConfig.py:ClickComponentName. After this has been defined, set the MAX_NETWORK_PKTS_PER_COMPONENT,
VPN_COMPONENTS_ORDER_INCOMING, VPN_COMPONENTS_ORDER_OUTGOING, Docker/Config.py:IMAGE_NAMES,
OVS/Config.py:KUBE_COMPONENT_TO_OVS_CONFIG, Kube/Config.py:KUBE_COMPONENT_TO_LABEL_VALUE. 

If the host was not prepared using the provided preparation script, you might also need to change
(OVS/Config.py:ovs_switch_name).

How to run
------------
Start the main.py script on a machine which has access to the nodes configured in Kube/Config.py.