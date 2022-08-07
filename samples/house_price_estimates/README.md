# Fybrik Based Housing Price Estimate Pipeline Sample

## Pipeline Overview

This is an enhancement of the pipeline for [house price prediction](https://github.com/kubeflow/pipelines/tree/master/samples/contrib/versioned-pipeline-ci-samples/kaggle-ci-sample).  We show how by integrating with [Fybrik](https://fybrik.io/v1.0/) the same pipeline benefits from transparent handling of non-functional requirements related to the reading and writing of data, such as the handling of credentials, automatic enforcement of data governance, and automatic allocation and cataloging of the new dataset containing the results.  

Please note that data is read/written via the arrow-flight protocol in this example.

A more detailed explanation of the goals, architecture, and demo screen shots can be found [here](https://drive.google.com/file/d/1xn7pGe5pEAEZxnIzDdom9r7K6s78alcP/view?usp=sharing).

## Prerequisits
* [Install kubeflow pipelines](https://www.kubeflow.org/docs/components/pipelines/installation/overview/#kubeflow-pipelines-standalone) configured to work with the demo katalog implementation.
* [Install Fybrik](https://fybrik.io/v1.0/get-started/quickstart/) using OPA as the governance engine
* Deploy [Datashim](https://datashim.io/)
```
kubectl apply -f kubectl apply -f https://raw.githubusercontent.com/datashim-io/datashim/master/release-tools/manifests/dlf-ibm-oc.yaml
```

## Usage

### Prepare Data Assets and Storage
From within the data folder perfrom the following steps.

Edit the following files to include the relevant details of where your data is stored.  They currently refer to an IBM cloud object store instance.
* house-price-demo-secret.yaml
* test-asset.yaml
* train-asset.yaml

Register in the Data Catalog (katalog) the training and testing data to be used by the pipeline, noting the catalog ID of each.
```
	Kubectl apply -f house-price-demo-secret.yaml -n kubeflow
	Kubectl apply -f test-asset.yaml -n kubeflow
    Kubectl apply -f train-asset.yaml -n kubeflow
```

[Register a storage account](https://fybrik.io/v1.0/samples/notebook-write/#deploy-resources-for-write-scenarios) in which the results can be written.  It assumes the same storage account as the train and test datasets, and thus uses the same secret.
```
    kubectl apply -f kfp-storage-account.yaml -n fybrik-system
```


### Register Governance Policies

From within the data folder run the following commands to register the data governance policies in the [OPA governance engine being used by Fybrik](https://fybrik.io/v1.0/tasks/using-opa/):

Read Policy:
```
    kubectl -n fybrik-system create configmap pii-read-policy --from-file=pii-read-policy.rego
		
    kubectl -n fybrik-system label configmap pii-read-policy openpolicyagent.org/policy=rego
		
    while [[ $(kubectl get cm pii-read-policy -n fybrik-system -o 'jsonpath={.metadata.annotations.openpolicyagent\.org/policy-status}') != '{"status":"ok"}' ]]; do echo "waiting for policy to be applied" && sleep 5; done
```


Write Policy:
```
    kubectl -n fybrik-system create configmap allow-write-policy --from-file=allow-write-policy.rego
		
    kubectl -n fybrik-system label configmap allow-write-policy openpolicyagent.org/policy=rego
		
    while [[ $(kubectl get cm allow-write-policy -n fybrik-system -o 'jsonpath={.metadata.annotations.openpolicyagent\.org/policy-status}') != '{"status":"ok"}' ]]; do echo "waiting for policy to be applied" && sleep 5; done

```

### Compile Pipeline
From within samples/house_price_estimate run the following, which will create a file called pipeline.yaml.
```
python3 pipeline.py
```

### Upload Pipeline
Upload the file pipeline.yaml via the Kubeflow Pipeline GUI.

See slide 17 of the [demo presentation](https://drive.google.com/file/d/1xn7pGe5pEAEZxnIzDdom9r7K6s78alcP/view?usp=sharing).

### Run the Pipeline
Create a pipeline run via the Kubeflow Pipeline GUI, providing the following parameters:
* train_dataset_id:  trainpii-csv
* test_dataset_id: testpii-csv
* namespace: kubeflow
* intent: PriceEstimates
* run_name: name of your choice - in lowercase

See slide 19 of the [demo presentation](https://drive.google.com/file/d/1xn7pGe5pEAEZxnIzDdom9r7K6s78alcP/view?usp=sharing).

### View Pipeline Run Details
Click on each step in the Kubeflow Pipeline GUI and view its log to see the output.  
* get-data-endpoints prints and returns the virtual endpoints for the 3 dataset (test, train, results)
* visualize-table prints a preview of the data, and you can see that the personal information has been obfuscated
* train-model runs trains the machine learning model and then runs it on the test data, printing out a sample of the results
* submit-result prints out the data catalog asset ID of the newly created asset containing the results

See slides 21-24 of the [demo presentation](https://drive.google.com/file/d/1xn7pGe5pEAEZxnIzDdom9r7K6s78alcP/view?usp=sharing).
