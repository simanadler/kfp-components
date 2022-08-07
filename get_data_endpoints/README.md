# Fybrik KFP component

This is a component that can be used in Kubeflow Pipelines to read test and training data, and to write the results of whatever
processing is done on that data **in a secure and governed fashion by leveraging Fybrik**

It is assumed that Fybrik is installed together with the chosen Data Catalog and Data Governance engine, and that ...
* training and testing datasets have been registered in the data catalog
* governance policies have been defined in the Data Governance engine

## Prerequisits
* [Install kubeflow pipelines](https://www.kubeflow.org/docs/components/pipelines/installation/overview/#kubeflow-pipelines-standalone)
* [Install Fybrik](https://fybrik.io/v1.0/get-started/quickstart/)

This component is compatible with Fybrik v1.0.


## Usage

The component receives the following parameters, all of which are strings.

Input:
* train_dataset_id -  data catalog ID of the dataset on which the ML model is trained
* test_dataset_id - data catalog ID of the dataset containing the testing data
* namespace - namespace in which the FybrikApplication yaml is applied (recommend using kubeflow namespace)
* intent - purpose for which the data is being used
* run_name - name of the run instance - lowercase letters only
* result_name - name of the result file to be generated

Outputs:
* train_endpoint - virtual endpoint used to read the training data
* test_endpoint - virtual endpoint used to read the testing data
* result_endpoint - virtual endpoint used to write the results 

### Example Pipeline Snippet 

```
def pipeline(
    test_dataset_id: str,
    train_dataset_id: str,
    run_name: str,
    intent: str,
    namespace: str
):
       
    # Where to store parameters passed between workflow steps
    result_name = "submission-" + str(run_name)

 ==>   getDataEndpointsOp = components.load_component_from_file('../../get_data_endpoints/component.yaml') 
    getDataEndpointsStep = getDataEndpointsOp(train_dataset_id=train_dataset_id, test_dataset_id=test_dataset_id, namespace=namespace, intent=intent, run_name=run_name, result_name=result_name)

    ...

    trainModelOp = components.load_component_from_file('./train_model/component.yaml')
    trainModelStep = trainModelOp(train_endpoint_path='%s' % getDataEndpointsStep.outputs['train_endpoint'],
                                test_endpoint_path='%s' % getDataEndpointsStep.outputs['test_endpoint'],
                                result_name=result_name,
                                result_endpoint_path='%s' % getDataEndpointsStep.outputs['result_endpoint'],
                                train_dataset_id=train_dataset_id,
                                test_dataset_id=test_dataset_id,
                                namespace=namespace)
```

