"""
step #1: get the endpoints of the data used
"""

#from msilib.schema import Component
from typing import List, OrderedDict
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint


# Wait until the FybrikApplication is ready, 
# and then get the endpoints for the datasets requested.
# If there is an error in FybrikApplication deployment or for one of the datasets
# then the endpoints will be empty and an error will be returned
def getEndpoints(run_name, train_data, test_data, k8s_api, namespace):

    # Read the status for specified FybrikApplication instance
    # Wait until it's either ready or there is an error
    fa_status = None
    train_status = None
    test_status = None
    while (fa_status == None) or ((train_status == None) or (test_status == None)):
        try:
            fa = k8s_api.get_namespaced_custom_object_status(
                group="app.fybrik.io", 
                version="v1alpha1",
                name=run_name,
                plural="fybrikapplications",
                namespace=namespace
            )
            # k8s status object exists
            if "status" in fa:
                fa_status = fa["status"]
                train_ready_condition = fa_status["assetStates"][namespace + "/" + train_data]["conditions"][0]["status"]
                test_ready_condition = fa_status["assetStates"][namespace + "/" + test_data]["conditions"][0]["status"]

                train_error_condition = fa_status["assetStates"][namespace + "/" + train_data]["conditions"][2]["status"]
                test_error_condition = fa_status["assetStates"][namespace + "/" + test_data]["conditions"][2]["status"]
                if "True" in train_error_condition:
                    train_status = "Error"

                if "True" in test_error_condition:
                    test_status = "Error"

                # check if assets are ready.  If not and there is no error, keep waiting
                if "True" in train_ready_condition and "True" in test_ready_condition:
                    train_status = "Ready"
                    test_status = "Ready"
        except ApiException as e:
            print("Exception when calling CustomObjectsApi->get_cluster_custom_object_status: %s\n" % e)
            return []  # return an empty list

    pprint(fa_status)

    # If ready, read the status of each of the datasets
    # TODO: If it's not ready, wait until it is - if there's no error condition
#    train_conditions = fa_status["assetStates"][namespace + "/" + train_data]["conditions"]
#    test_conditions = fa_status["assetStates"][namespace + "/" + test_data]["conditions"]

    endpoint_dict = {}
    if train_status == "Ready":
        train_endpoint = endpoint_dict[namespace + "/" + train_data] = fa_status["assetStates"][namespace + "/" + train_data]["endpoint"]["fybrik-arrow-flight"]
        train_url = train_endpoint["scheme"] + "://" + train_endpoint["hostname"] + ":" + train_endpoint["port"]
        endpoint_dict[namespace + "/" + train_data] = train_url

    if test_status == "Ready":
        test_endpoint = endpoint_dict[namespace + "/" + test_data] = fa_status["assetStates"][namespace + "/" + test_data]["endpoint"]["fybrik-arrow-flight"]
        test_url = test_endpoint["scheme"] + "://" + test_endpoint["hostname"] + ":" + test_endpoint["port"]       
        endpoint_dict[namespace + "/" + test_data] = test_url

    # Return the two endpoints for the two datasets
    return endpoint_dict

# Create a FybrikApplication with the datasets requested and the context
def createFybrikApplicationObj(run_name, intent, train_data, test_data, namespace):
    fybrikApp = {
        "apiVersion": "app.fybrik.io/v1alpha1",
        "kind": "FybrikApplication",
        "metadata": {
            "name": run_name,
            "labels": {
                "app": run_name
            }
        },
        "spec": {
            "selector": {
                "workloadSelector": {
                    "matchLabels": {
                        "app": run_name
                    }
                }
            },
            "appInfo": {
                "intent": intent
            },
            "data": [
                {
                    "dataSetID": namespace + "/" + test_data,
                    "requirements": {
                        "interface": {
                            "protocol": "fybrik-arrow-flight"
                        }
                    }
                },
                {
                    "dataSetID": namespace + "/" + train_data,
                    "requirements": {
                        "interface": {
                            "protocol": "fybrik-arrow-flight"
                        }
                    }
                }
            ]
        }
    }
    return fybrikApp

# Apply the FybrikApplication using the Kubernetes SDK
def createFybrikApplication(run_name, intent, train_data, test_data, namespace, k8s_api):
 
    # Create the FybrikApplication yaml
    fa = createFybrikApplicationObj(run_name, intent, test_data, train_data, namespace)

    try:
        resp = k8s_api.create_namespaced_custom_object(body=fa, namespace=namespace, group="app.fybrik.io", version="v1alpha1", plural="fybrikapplications")
        return True
    except ApiException as e:
        print("Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)
        return False
 
if __name__ == '__main__':
 
    # Get the arguments passed to the component
    # catalog ID of the files containing the training and testing data
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_dataset_id', type=str)
    parser.add_argument('--train_dataset_id', type=str)
    parser.add_argument('--run_name', type=str)
    parser.add_argument('--intent', type=str)
    parser.add_argument('--namespace', type=str)
    args = parser.parse_args()

    # Get access to kubernetes
    config.load_kube_config()
    k8s_api = client.CustomObjectsApi()

    # When the status is read, get the endpoints from the FybrikApplication status
    succeeded = createFybrikApplication(args.run_name, args.intent, args.train_dataset_id, args.test_dataset_id, args.namespace, k8s_api)


    if (succeeded):
        end_points = getEndpoints(args.run_name, args.train_dataset_id, args.test_dataset_id, k8s_api, args.namespace)
        if len(end_points) == 0:
            print("No endpoints generated")
        else:
            print("endpoints: ", end_points)
 
    