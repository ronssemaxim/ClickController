
import Logger
from Kube import KubeAdapter
from Kube.Config import KUBE_COMPONENT_TO_LABEL_VALUE
from MainConfig import KUBE_COMPONENT_LABEL_NAME


def get_all_pods(label_dict=None):
    return KubeAdapter.get_all_pods(label_dict)


def get_pods_on_nodes():
    pods = get_all_pods({
        # FIXME
        KUBE_COMPONENT_LABEL_NAME: list(KUBE_COMPONENT_TO_LABEL_VALUE.values())
    })

    if not pods:
        return False

    node_to_pods = {}
    for pod in (pods.items()):
        node_name = pod.spec.node_name
        if node_name in node_to_pods:
            Logger.log("Pod", "Appending pod to list of nodes in host " + node_name, 8)
            node_to_pods[node_name].append(pod)
        else:
            Logger.log("Creating pod list of nodes for host " + node_name, 8)
            node_to_pods[node_name] = [{
                "name": pod.metadata.name,
                "labels": pod.metadata.labels,
                "containers": pod.spec.containers
            }]
    return node_to_pods
