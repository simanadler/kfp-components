"""
step #1: get the endpoints of the data used
"""

#from msilib.schema import Component
from tokenize import String
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint

def _make_parent_dirs_and_return_path(file_path: str):
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return file_path

# Wait until the FybrikApplication is ready, 
# and then get the endpoints for the datasets requested, and for writing the results.
# If there is an error in FybrikApplication deployment or for one of the datasets
# then the endpoints will be empty and an error will be returned
def getEndpoints(args, k8s_api):

    # Read the status for specified FybrikApplication instance
    # Wait until it's either ready or there is an error
    fa_status = None
    train_status = None
    test_status = None
    result_status = None
    train_endpoint = ""
    test_endpoint = ""
    result_endpoint = ""
    result_catalogid = ""

    while (fa_status == None) or ((train_status == None) or (test_status == None)):
        try:
            fa = k8s_api.get_namespaced_custom_object_status(
                group="app.fybrik.io", 
                version="v1beta1",
                name=args.run_name,
                plural="fybrikapplications",
                namespace=args.namespace
            )
            # k8s status object exists
            if "status" in fa:
                fa_status = fa["status"]
                train_ready_condition = fa_status["assetStates"][args.namespace + "/" + args.train_dataset_id]["conditions"][0]["status"]
                test_ready_condition = fa_status["assetStates"][args.namespace + "/" + args.test_dataset_id]["conditions"][0]["status"]
                result_ready_condition = fa_status["assetStates"][args.result_name]["conditions"][0]["status"]
 
                # Check if the status of the 3 is "ready".  If so, we're good to go.
                if "True" in train_ready_condition:
                    train_status = "Ready"

                if "True" in test_ready_condition:
                    test_status = "Ready"

                if "True" in result_ready_condition:
                    result_status = "Ready"

                # Check for errors
                train_error_condition = fa_status["assetStates"][args.namespace + "/" + args.train_dataset_id]["conditions"][2]["status"]
                test_error_condition = fa_status["assetStates"][args.namespace + "/" + args.test_dataset_id]["conditions"][2]["status"]
                result_error_condition = fa_status["assetStates"][args.result_name]["conditions"][2]["status"]
                if "True" in train_error_condition:
                    train_status = "Error"

                if "True" in test_error_condition:
                    test_status = "Error"

                if "True" in result_error_condition:
                    result_status = "Error"

                # Check for deny
                train_deny_condition = fa_status["assetStates"][args.namespace + "/" + args.train_dataset_id]["conditions"][1]["status"]
                test_deny_condition = fa_status["assetStates"][args.namespace + "/" + args.test_dataset_id]["conditions"][1]["status"]
                result_deny_condition = fa_status["assetStates"][args.result_name]["conditions"][1]["status"]
                if "True" in train_deny_condition:
                    train_status = "Deny"

                if "True" in test_deny_condition:
                    test_status = "Deny"

                if "True" in result_deny_condition:
                    result_status = "Deny"
                    
        except ApiException as e:
            print("Exception when calling CustomObjectsApi->get_cluster_custom_object_status: %s\n" % e)
            return []  # return an empty list

    pprint(fa_status)

    # If ready, read the endpoint of each of the datasets
    if train_status == "Ready":
        train_struct = fa_status["assetStates"][args.namespace + "/" + args.train_dataset_id]["endpoint"]["fybrik-arrow-flight"]
        train_endpoint = train_struct["scheme"] + "://" + train_struct["hostname"] + ":" + train_struct["port"]

    if test_status == "Ready":
        test_struct = fa_status["assetStates"][args.namespace + "/" + args.test_dataset_id]["endpoint"]["fybrik-arrow-flight"]
        test_endpoint = test_struct["scheme"] + "://" + test_struct["hostname"] + ":" + test_struct["port"]       

    if result_status == "Ready":
        result_struct = fa_status["assetStates"][args.result_name]["endpoint"]["fybrik-arrow-flight"]
        result_endpoint = result_struct["scheme"] + "://" + result_struct["hostname"] + ":" + result_struct["port"]       
        result_catalogid = fa_status["assetStates"][args.result_name]["catalogedAsset"]
 
    print("train_status is " + train_status + ", train_endpoint: " + train_endpoint)
    print("train_status is " + test_status + ", test_endpoint: " + test_endpoint)
    print("result_status is " + result_status + ", result_endpoint: " + result_endpoint)
    print("result_catalogid is %s\n" % result_catalogid)

    # Return the endpoints for the input and ouptut datasets - by writing to files
    with open(args.train_endpoint_path, 'w') as train_file:
        train_file.write(train_endpoint)
    with open(args.test_endpoint_path, 'w') as test_file:
        test_file.write(test_endpoint)
    with open(args.result_endpoint_path, 'w') as result_file:
        result_file.write(result_endpoint)
    
    # Return the id of the new catalog entry created for the results dataset
    with open(args.result_catalogid_path, 'w') as result_catalogid_file:
        result_catalogid_file.write(result_catalogid)


# Create a FybrikApplication with the datasets requested and the context
def createFybrikApplicationObj(args):
    fybrikApp = {
        "apiVersion": "app.fybrik.io/v1beta1",
        "kind": "FybrikApplication",
        "metadata": {
            "name": args.run_name,
            "labels": {
                "app": args.run_name
            }
        },
        "spec": {
            "selector": {
                "workloadSelector": {
                    "matchLabels": {
                        "app": args.run_name
                    }
                }
            },
            "appInfo": {
                "intent": args.intent
            },
            "data": [
                {
                    "dataSetID": args.namespace + "/" + args.test_dataset_id,
                    "flow": "read",
                    "requirements": {
                        "interface": {
                            "protocol": "fybrik-arrow-flight"
                        }
                    }
                },
                {
                    "dataSetID": args.namespace + "/" + args.train_dataset_id,
                    "flow": "read",
                    "requirements": {
                        "interface": {
                            "protocol": "fybrik-arrow-flight"
                        }
                    }
                },
                {
                    "dataSetID": args.result_name,
                    "flow": "write",
                    "requirements": {
                        "interface": {
                            "protocol": "fybrik-arrow-flight"
                        },
                        "flowParams": {
                            "isNewDataSet": True,
                            "catalog": args.namespace
                        }
                    }
                }
            ]
        }
    }
    return fybrikApp

# Apply the FybrikApplication using the Kubernetes SDK
def createFybrikApplication(args, k8s_api):
 
    # Create the FybrikApplication yaml
    fa = createFybrikApplicationObj(args)
    print("FybrikApplication: \n")
    print(fa)

    try:
        resp = k8s_api.create_namespaced_custom_object(body=fa, namespace=args.namespace, group="app.fybrik.io", version="v1beta1", plural="fybrikapplications")
        return True
    except ApiException as e:
        print("Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)
        return False


def doFybrikMagic(args):
    # Get access to kubernetes
    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except config.ConfigException:
            raise Exception("Could not configure kubernetes python client")

    k8s_api = client.CustomObjectsApi()

    # When the status is ready, get the endpoints from the FybrikApplication status
    succeeded = createFybrikApplication(args, k8s_api)

    if (succeeded):
        getEndpoints(args, k8s_api)
    else:
        # Return empty endpoints
        with open(args.train_endpoint_path, 'w') as train_file:
            train_file.write("")
        with open(args.test_endpoint_path, 'w') as test_file:
            test_file.write("")
        with open(args.result_endpoint_path, 'w') as result_file:
            result_file.write("")
        with open(args.result_catalogid_path, 'w') as result_catalogid_file:
            result_catalogid_file.write("")
   


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
 #   parser.add_argument('--train_endpoint_path', type=str)
 #   parser.add_argument('--test_endpoint_path', type=str)
    parser.add_argument("--test_endpoint", dest="test_endpoint_path", type=_make_parent_dirs_and_return_path, required=True, default=argparse.SUPPRESS)
    parser.add_argument("--train_endpoint", dest="train_endpoint_path", type=_make_parent_dirs_and_return_path, required=True, default=argparse.SUPPRESS)
    parser.add_argument("--result_name", type=str, required=True, default=argparse.SUPPRESS)
    parser.add_argument("--result_endpoint", dest="result_endpoint_path", type=_make_parent_dirs_and_return_path, required=True, default=argparse.SUPPRESS)
    parser.add_argument("--result_catalogid", dest="result_catalogid_path", type=_make_parent_dirs_and_return_path, required=True, default=argparse.SUPPRESS)
    args = parser.parse_args()

    # print("Calling doFybrikMagic to create the FybrikApplication, apply it, and read its status")
    outputs = doFybrikMagic(args)

    # Calling testFunc to write static output
    # testFunc()

