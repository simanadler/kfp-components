from pathlib import Path
from pickletools import read_stringnl_noescape


def datatable(
    train_endpoint_path,
    train_dataset_id
):
    import pandas as pd
    import json
    import pyarrow.flight as fl

    # Read the endpoint for the training data from the temporary storage from the previous step
    try:
        with open(train_endpoint_path, 'r') as train_endpoint_file:
            endpoint = train_endpoint_file.read()
            train_endpoint_file.close()
    except Exception as e:
        print("Error getting endpoint from file: %s\n" % e)
        print("endpoint path = %s\n" % train_endpoint_path)
        return

    # Read the file from cos using arrow-flight
    # Create a Flight client
    try:
        client = fl.connect(endpoint)
    except Exception as e:
        print("Exception when connection to arrow flight server %s\n" % e)
        print("train data endpoint: %s\n" % args.train_endpoint)
        return 
    

    # Prepare the request
    data_id = 'kubeflow/' + args.train_dataset_id
    request = { 'asset': data_id } 

    # Send request and fetch result as a pandas DataFrame
    try:
        info = client.get_flight_info(fl.FlightDescriptor.for_command(json.dumps(request)))
        info = client.get_flight_info(fl.FlightDescriptor.for_command(json.dumps(request)))
        reader: fl.FlightStreamReader = client.do_get(info.endpoints[0].ticket)
        train_file: pd.DataFrame = reader.read_pandas()
    except Exception as e:
        print("Exception sending read request to arrow flight server %s\n" % e)
        print("train data endpoint: %s\n" % endpoint)
        return

 #   train_file = pd.read_csv(train_file_path)
    header = train_file.columns.tolist()
    metadata = {
        'outputs' : [{
            'type': 'table',
            'storage': 'cos',
            'format': 'csv',
            'header': header,
            'source': endpoint
            }]
        }

 #   with open(mlpipeline_metrics, 'w') as f:
 #       json.dump(metadata, f)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_endpoint', dest="train_endpoint_path", type=str, required=True, default=argparse.SUPPRESS)
    parser.add_argument('--train_dataset_id', dest="train_dataset_id", type=str, required=True, default=argparse.SUPPRESS)
#    parser.add_argument('--mlpipeline_metrics', type=str)
    args = parser.parse_args()

 #   datatable(args.train_file_path, args.train_dataset_id, args.mlpipeline_metrics)
    datatable(args.train_endpoint_path, args.train_dataset_id)
