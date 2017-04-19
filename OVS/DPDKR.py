"""
OVS/DPDKR.py. Keeps track of the free DPDKR ports, using a linked list

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""

from PyClickController.OVS.Switch import get_ovs_to_dpdkr_nr


# Node class used to define the linked list
class Node:
    # carge = data in this node, next = next node or none if no next node
    def __init__(self, cargo=None, next=None):
        self.data = cargo
        self.next = next

    # print this node and all next nodes
    def __str__(self):
        return str(self.data) + " -> " + str(self.next)


class DPDKR:
    def __init__(self):
        # init linked list
        self.free_ports = None
        # fetch ovs ports from the host
        # loop over each ovs->dpdkr mapping, add to the linked list
        for ovs, dpdkr in get_ovs_to_dpdkr_nr().items():
            self.free_ports = Node(dpdkr, self.free_ports)

    def get_next(self):
        """
        Get a free dpdkr port
        :return: a free dpdkr port (numeric)
        :raises IndexError if no DPDKR ports are free
        """
        if self.free_ports:
            ret = self.free_ports.data
            self.free_ports = self.free_ports.next
            return ret
        else:
            raise IndexError("No free dpdkr ports found")

    def add_free_port(self, nr):
        """
        Add a DPDKR port to the list of free ports
        :param nr: numeric port number
        """
        self.free_ports = Node(nr, self.free_ports)

    def __str__(self):
        return "DPDKR free port list: " + str(self.free_ports)
