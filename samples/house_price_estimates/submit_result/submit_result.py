"""
step #4: submit result to kaggle
"""
import kfp

def _make_parent_dirs_and_return_path(file_path: str):
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return file_path


def submit_result(
    result_catalogid_path,
    markdown_artifact: Output[Markdown]
):
    # Read the catalog id received from a previous step in the pipeline
    catalog_asset_id = ""
    try:
        with open(result_catalogid_path, 'r') as result_catalogid_file:
            catalog_asset_id = result_catalogid_file.read()
            result_catalogid_file.close()
    except Exception as e:
        print("Error getting catalog id from file: %s\n" % e)
        print("catalog id path = %s\n" % result_catalogid_path)
        return

    print("The results have been generated and have been cataloged as data asset %s\n", catalog_asset_id)
    markdown_content = "## The results have been generated and have been cataloged as data asset " + catalog_asset_id + "\n\n"

    metadata = {
        'outputs' : [
            # Markdown that is hardcoded inline
            {
                'storage': 'inline',
                'source': markdown_content,
                'type': 'markdown',
            }
        ]
    }

    #  Writes to the file used by kubeflow pipeline to display metadata
    import json
    with open('/mlpipeline-ui-metadata.json', 'w') as f:
        json.dump(metadata, f)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--result_catalogid", dest="result_catalogid_path", type=_make_parent_dirs_and_return_path, required=True, default=argparse.SUPPRESS)
    args = parser.parse_args()

    submit_result(args.result_catalogid_path)
    