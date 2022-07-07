import kfp.dsl as dsl
import kfp.components as components
from kubernetes import client as k8s_client
import os

@dsl.pipeline(
    name = "Fybrik housing price estimate pipeline",
    description = "Pipeline that provides data policy governed access to cataloged data, analyses data, trains model, and writes the results and catalogs them"
)
def houseprice_pipeline(
    test_dataset_id: str,
    train_dataset_id: str,
    run_name: str,
    intent: str
):
       
    # Where to store parameters passed between workflow steps
    train_endpoint_path = './train.txt'
    test_endpoint_path = './test.txt'
    metadata_path = 'mlpipeline_metadata.json'
    namespace = 'kubeflow'
   
#    downloadDataOp = components.load_component_from_file('./download_dataset/component.yaml')
#    downloadDataStep = downloadDataOp(bucket_name='test-bucket').apply(use_gcp_secret('user-gcp-sa'))
    getDataEndpointsOp = components.load_component_from_file('../../get_data_endpoints/component.yaml')
    getDataEndpointsStep = getDataEndpointsOp(train_dataset_id=train_dataset_id, test_dataset_id=test_dataset_id, namespace=namespace, intent=intent, run_name=run_name)
 
    visualizeTableOp = components.load_component_from_file('./visualize_table/component.yaml')
 #   visualizeTableStep = visualizeTableOp(train_endpoint_path='%s'% getDataEndpointsStep.outputs['train_endpoint'], train_dataset_id=train_dataset_id, mlpipeline=mlpipeline)
 #    visualizeTableStep = visualizeTableOp(train_endpoint_path='%s'% getDataEndpointsStep.outputs['train_endpoint'], train_dataset_id=train_dataset_id)
    visualizeTableStep = visualizeTableOp(train_endpoint='%s'% getDataEndpointsStep.outputs['train_endpoint'], train_dataset_id=train_dataset_id)

if __name__ == '__main__':

    # Set environment values to ensure persistent volumes used to pass parameters are allocated successfully
 #   os.environ["DEFAULT_STORAGE_CLASS"] = "standard"
 #   os.environ["DEFAULT_ACCESSMODES"] = "ReadWriteOnce"
 #   os.environ["DEFAULT_STORAGE_SIZE"] = "2Gi"
 
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_dataset_id', type=str)
    parser.add_argument('--train_dataset_id', type=str)
    parser.add_argument('--run_name', type=str)
    parser.add_argument('--intent', type=str)

    args = parser.parse_args()
    from kfp_tekton.compiler import TektonCompiler
 
    TektonCompiler().compile(houseprice_pipeline, __file__.replace('.py', '.yaml'))