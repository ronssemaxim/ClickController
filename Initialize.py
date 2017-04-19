"""
Initialize.py. Configures the initial deployments and their flows

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import Logger
from Kube.Config import KUBE_COMPONENT_TO_LABEL_VALUE
from Kube.Deployment import create_deployment_for_component, delete_all_deployments
from MainConfig import DO_INIT_DEPLOYMENTS
from OVS.Flow import create_component_flows


def create_initial_deployments(dpdkr_to_ovs_nr):
    """
    Create initial deployments and configures the flows between the containers
    :param dpdkr_to_ovs_nr:
    :return: a dictionary of components, with a list of deployments for each component. Eg:
    {Encr: [{name:, dpdkr:, ovsPort:, type:}, ...], ... , "max_dpdkr": 123}
    """
    ret_dict = {}
    # delete old deployments
    Logger.log("Init", "Deleting old Kubernetes deployments", 2)
    if DO_INIT_DEPLOYMENTS:
        delete_all_deployments()

    Logger.log("Init", "Creating new deployments and rings", 2)
    max_dpdkr = 0
    for (kubeComponentType, kubeComponentName) in KUBE_COMPONENT_TO_LABEL_VALUE.items():
        deployment = create_deployment_for_component(kubeComponentType, dpdkr_to_ovs_nr)
        ret_dict[kubeComponentType] = [deployment]
        max_dpdkr = deployment["dpdkr"]

    # Create the OVS flows between the deployments
    create_component_flows(ret_dict)

    ret_dict["max_dpdkr"] = max_dpdkr  # set the highest DPDKR number
    return ret_dict
