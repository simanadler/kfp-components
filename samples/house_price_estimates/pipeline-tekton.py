import kfp.dsl as dsl
import kfp.components as components

@dsl.pipeline(
    name = "Fybrik housing price estimate pipeline",
    description = "Pipeline that provides data policy governed access to cataloged data, analyses data, trains model, and writes the results and catalogs them"
)

def get_current_namespace():
    import kubernetes
    import os

    ns_path = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
    if os.path.exists(ns_path):
        with open(ns_path) as f:
            return f.read().strip()
    try:
        _, active_context = kubernetes.config.list_kube_config_contexts()
        return active_context["context"]["namespace"]
    except KeyError:
        return "kubeflow"

def houseprice_pipeline(
    test_dataset_id: str,
    train_dataset_id: str
):
    # Get the namespace in which kfp is running
    namespace = get_current_namespace()

    # Get the ID of the run.  Make sure it's lower case and starts with a letter for our use
    run_name = "run-" + dsl.RUN_ID_PLACEHOLDER.lower()

    # Where to store parameters passed between workflow steps
    result_name = "submission-" + str(run_name)

    getDataEndpointsOp = components.load_component_from_file('../../get_data_endpoints/component.yaml')
    getDataEndpointsStep = getDataEndpointsOp(train_dataset_id=train_dataset_id, test_dataset_id=test_dataset_id, namespace=namespace, run_name=run_name, result_name=result_name)
    
    visualizeTableOp = components.load_component_from_file('./visualize_table/component.yaml')
    visualizeTableStep = visualizeTableOp(train_endpoint='%s'% getDataEndpointsStep.outputs['train_endpoint'], train_dataset_id=train_dataset_id, namespace=namespace)
    visualizeTableStep.after(getDataEndpointsStep)

    trainModelOp = components.load_component_from_file('./train_model/component.yaml')
    trainModelStep = trainModelOp(train_endpoint_path='%s' % getDataEndpointsStep.outputs['train_endpoint'],
                                test_endpoint_path='%s' % getDataEndpointsStep.outputs['test_endpoint'],
                                result_name=result_name,
                                result_endpoint_path='%s' % getDataEndpointsStep.outputs['result_endpoint'],
                                train_dataset_id=train_dataset_id,
                                test_dataset_id=test_dataset_id,
                                namespace=namespace)
    trainModelStep.after(visualizeTableStep)

    sumbitResultOp = components.load_component_from_file('./submit_result/component.yaml')
    submitResultStep = sumbitResultOp(getDataEndpointsStep.outputs['result_catalogid'])
    submitResultStep.after(trainModelStep)
 
if __name__ == '__main__':

    # Set environment values to ensure persistent volumes used to pass parameters are allocated successfully 
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_dataset_id', type=str)
    parser.add_argument('--train_dataset_id', type=str)

    args = parser.parse_args()
    from kfp_tekton.compiler import TektonCompiler
 
    TektonCompiler().compile(houseprice_pipeline, __file__.replace('.py', '.yaml'))