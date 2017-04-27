"""
Kube/Deployment.py. Used to start/stop kubernetes deployments

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""

import Logger
from DelayedInvoke import DelayedInvoke
from Docker.Config import IMAGE_NAMES
from Kube import KubeAdapter
from Kube.Config import KUBE_COMPONENT_TO_LABEL_VALUE
from MainConfig import KUBE_COMPONENT_LABEL_NAME, KUBE_DEPLOYMENT_PREFIX, DO_INIT_DEPLOYMENTS, \
    DELETE_DEPLOYMENT_AFTER, KUBE_DPDK_RING_LABEL_NAME
from OVS.DPDKR import DPDKR
from SSH import get_ssh_con_master

dpdkr = DPDKR()


def get_all_deployments():
    """
    get all deployments
    :return: all deployments straight from the k8s api as a python dictionary
    """
    return KubeAdapter.get_all_deployments()


def create_deployment_for_component(component_type, dpdkr_to_ovs_nr):
    """
    Create a k8s deployment for the specified component.
    :param component_type: the component type for which to create the deployment
    :param dpdkr_to_ovs_nr: dictionary of DPDK Ring number to Open vSwitch port number. Used to return the ovsPort
    :return: details for the created deployment: {name:, dpdkr:, ovsPort:, type:}
    """
    component_label_value = KUBE_COMPONENT_TO_LABEL_VALUE[component_type]
    next_dpdkr = dpdkr.get_next()
    kube_deployment_name =\
        KUBE_DEPLOYMENT_PREFIX + "-" + KUBE_COMPONENT_TO_LABEL_VALUE[component_type] + "-" + str(next_dpdkr)
    kube_component_type = str(component_type)

    Logger.log("Init", "Creating deployment for component " + component_label_value, 4)
    Logger.log("Init", "    ->deployment name is " + kube_deployment_name, 4)
    Logger.log("Init", "    ->component type is " + kube_component_type, 4)
    Logger.log("Init", "    ->image name is " + IMAGE_NAMES[component_type], 4)
    Logger.log("Init", "    ->label name is " + KUBE_COMPONENT_LABEL_NAME, 4)
    if DO_INIT_DEPLOYMENTS:
        create_deployment(kube_deployment_name, IMAGE_NAMES[component_type], {
            KUBE_COMPONENT_LABEL_NAME: component_label_value,
            KUBE_DPDK_RING_LABEL_NAME: str(next_dpdkr)
        })

    return {
            "name": kube_deployment_name,
            "dpdkr": next_dpdkr,
            "ovsPort": dpdkr_to_ovs_nr[next_dpdkr],  # get actual OVS number of port (!= dpdk nr)
            "type": kube_component_type
        }


def create_deployment(deployment_name, image_name, labels):
    """
    Create a single k8s deployment
    :param deployment_name: name for this deployment
    :param image_name: image name for this deployment (see Docker/Config.py)
    :param labels: dictionary of labels, specified as name: value
    :return:
    """
    Logger.log("Dep", "Creating new deployment with name " + deployment_name + ", using image " + image_name)
    return KubeAdapter.create_deployment({
        "apiVersion": "extensions/v1beta1",
        "kind": "Deployment",
        "metadata": {
            "namespace": "default",
            "name": deployment_name
        },
        "spec": {
            "replicas": 1,
            "template": {
                "metadata": {
                    "labels": labels
                },
                "spec": {
                    "containers": [
                        {
                            "name": deployment_name,
                            "image": "ronssemaxim/customclick",
                            "imagePullPolicy": "IfNotPresent",
                            "ports": [],
                            "securityContext": {
                                "privileged": True
                            },
                            "volumeMounts": [
                                {
                                    "name": "pci-drivers",
                                    "mountPath": "/sys/bus/pci/drivers"
                                },
                                {
                                    "name": "kernel-hugepages",
                                    "mountPath": "/sys/kernel/mm/hugepages"
                                },
                                {
                                    "name": "system-node",
                                    "mountPath": "/sys/devices/system/node"
                                },
                                {
                                    "name": "devices",
                                    "mountPath": "/dev"
                                },
                                {
                                    "name": "mnt-hugepages",
                                    "mountPath": "/mnt/huge"
                                },
                                {
                                    "name": "mnt-hugepages-config",
                                    "mountPath": "/var/run"
                                },
                                {
                                    "name": "podinfo",
                                    "mountPath": "/etc/kubernetes"
                                }
                            ]
                        }
                    ],
                    "volumes": [
                        {
                            "name": "pci-drivers",
                            "hostPath": {
                                "path": "/sys/bus/pci/drivers"
                            }
                        },
                        {
                            "name": "kernel-hugepages",
                            "hostPath": {
                                "path": "/sys/kernel/mm/hugepages"
                            }
                        },
                        {
                            "name": "system-node",
                            "hostPath": {
                                "path": "/sys/devices/system/node"
                            }
                        },
                        {
                            "name": "devices",
                            "hostPath": {
                                "path": "/dev"
                            }
                        },
                        {
                            "name": "mnt-hugepages",
                            "hostPath": {
                                "path": "/mnt/huge"
                            }
                        },
                        {
                            "name": "mnt-hugepages-config",
                            "hostPath": {
                                "path": "/var/run"
                            }
                        },
                        {
                            "name": "podinfo",
                            "downwardAPI": {
                                "items": [
                                    {
                                        "path": "labels",
                                        "fieldRef": {
                                            "fieldPath": "metadata.labels"
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    })


def delete_all_deployments():
    """
    Deletes all k8s deployments who's name contains KUBE_DEPLOYMENT_PREFIX
    TODO: Grep only when deployment starts with the prefix, not anywhere. Also append "-" to the prefix
    """
    get_ssh_con_master().exec("sudo kubectl delete deployment $(kubectl get deployments | cut -d' ' -f1 | grep " +
                              KUBE_DEPLOYMENT_PREFIX + ")", mayFail=True)


def delete_deployment(deployment, use_cached_ssh_con=True):
    """
    Delete deployment by it's details
    :param deployment: details as returned from create_deployment
    :param use_cached_ssh_con: whether or not to use a cached SSH connection (set to False when used in a thread)
    """
    get_ssh_con_master(cached=use_cached_ssh_con).exec(
        "sudo kubectl delete deployment \"" + deployment["name"] + "\"", mayFail=False)
    dpdkr.add_free_port(deployment["dpdkr"])  # free dpdkr
    '''
    TODO: Delete deployment is broken since kubelet v1.6.0-00 ==> should revert to 1.5.6-00 or find fix
    return KubeAdapter.delete_deployment(name, {
        "apiVersion": "apps/v1beta1",
        "kind": "Deployment",
        "metadata": {
            "namespace": "default",
            "name": name
        }
    })'''


def delete_deployment_delayed(deployment):
    """
    Delete a deployment after DELETE_DEPLOYMENT_AFTER is expired
    :param deployment: details as returned from create_deployment
    :return: thread object
    """
    thread = DelayedInvoke(delete_deployment, deployment, False, exec_after=DELETE_DEPLOYMENT_AFTER)
    thread.start()
    return thread
