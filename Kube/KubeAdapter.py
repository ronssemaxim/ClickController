"""
KubeAdapter.py. Used to execute actions on the k8s API

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import Logger
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def get_api_client(beta=False, apps=False):
    """
    Get normal k8s API client
    :param beta: if true, return v1beta1 client
    :param apps: if true, return apps client
    :return: API client
    """
    try:
        config.load_kube_config(config_file="Kube/kube-config.conf")

        if beta:
            return client.ExtensionsV1beta1Api()
        if apps:
            return client.AppsV1beta1Api()
        else:
            client.CoreV1Api()
    except ApiException as e:
        Logger.log("Adapter", "Exception when creating api object: " + str(e), 1)
        return False


def get_beta_client():
    """
    get v1beta1 API client
    :return: the client
    """
    return get_api_client(True)


def get_apps_client():
    """
    get apps API client
    :return: the client
    """
    return get_api_client(False, True)


def get_all_deployments():
    """
    Get all deployments
    :return: json output
    """
    try:
        return get_beta_client().list_namespaced_deployment("default", pretty="false")
    except ApiException as e:
        Logger.log("Adapter", "Exception when calling ExtensionsV1beta1Api->list_namespaced_deployment: " + str(e), 1)
        return False


def create_deployment(json):
    """
    Create a deployment
    :param json: json body
    :return: json output
    """
    try:
        return get_beta_client().create_namespaced_deployment("default", json)
    except ApiException as e:
        Logger.log("Adapter", "Exception when calling ExtensionsV1beta1Api->create_namespaced_deployment: " + str(e), 1)
        return False


def delete_deployment(name, json):
    """
    Delete a deployment
    :param name: name of the deployment to delete
    :param json: body (DeleteOptions)
    :return: json output
    """
    try:
        return get_apps_client().delete_namespaced_deployment(name, "default", json)
    except ApiException as e:
        Logger.log("Adapter", "Exception when calling ExtensionsV1beta1Api->delete_namespaced_deployment: " + str(e), 1)
        return False


def get_all_pods(label_dict=None):
    """
    Get all pods.
    :param label_dict: label selector
    :return: json output
    """
    try:

        if label_dict is not None:
            selector = ""
            for (labelName, labelValues) in label_dict.items():
                selector += labelName + " in (" + ",".join(labelValues) + "),"

            selector = selector[:-1]
            Logger.log("Adapter", "Get all pods with selector " + selector, 8)
            return get_api_client().list_pod_for_all_namespaces(label_selector=selector)
        else:
            return get_api_client().list_pod_for_all_namespaces()
    except ApiException as e:
        Logger.log("Adapter", "Exception when calling CoreV1Api->list_pod_for_all_namespaces: %s\n" + str(e), 1)
        return False


def get_all_nodes():
    """
    Get all nodes
    :return: json output
    """
    try:
        return get_api_client().list_node()
    except ApiException as e:
        Logger.log("Adapter", "Exception when calling CoreV1Api->list_node: " + str(e), 1)
        return False
