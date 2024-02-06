from time import time
from uuid import uuid1
import logging
from datetime import datetime, timedelta, timezone
from json import dumps, loads
from pathlib import Path
import functions_framework
from flask import abort, g, make_response
from flask_expects_json import expects_json
from os import environ
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from util_input_validation import schema, Config
from util_helpers import impersonate_account, create_outgoing_file_ref, handle_bad_request,handle_exception,handle_not_found
from deepgram import Deepgram
from normalize import normalise_deepgram

#Libraries for Azure
import azure.functions as func
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from werkzeug.exceptions import InternalServerError, BadRequest, NotFound


### GLOBAL Vars

### Env Vars
### service = environ.get("K_SERVICE")

### Instance-wide storage Vars
instance_id = str(uuid1())
run_counter = 0

connection_string=os.environ["StorageAccountConnectionString"]
storage_client=BlobServiceClient.from_connection_string(connection_string)

start_time = time()  
time_cold_start = time() - start_time


#### curl check
import subprocess

# def execute_curl(url):
#     try:
#         # Run the curl command and capture the output
#         result = subprocess.run(['curl', '-I', url], capture_output=True, text=True, check=True)

#         # Print the result (headers) of the curl command
#         print(result.stdout)

#         # Check the return code to determine success or failure
#         if result.returncode == 0:
#             print("Curl command executed successfully")
#         else:
#             print(f"Curl command failed with return code: {result.returncode}")

#     except subprocess.CalledProcessError as e:
#         # Handle exceptions, if the curl command fails
#         print(f"Error executing curl command: {e}")
#         print("Error output:")
#         print(e.stderr)
    
# # Example usage
# url_to_check = "http://stg-deepgram.dg.stg.usw1.cloud.247-inc.net:8080/v2"
# execute_curl(url_to_check)


### MAIN
# @functions_framework.http
# @expects_json(schema)
# def main(request):

app = func.FunctionApp()
@app.function_name(name="wf_transcribe_HttpTrigger1")
@app.route(route="wf_transcribe_HttpTrigger1")

def main(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """

    ### Input Variables
    global run_counter
    run_counter += 1
    request_recieved = datetime.now(timezone.utc)
    request_json = req.get_json()
    CONFIG = Config(request_json)
    del request_json
    context = {
        **CONFIG.context.toJson(),
        "instance": instance_id,
        "instance_run": run_counter,
        "request_recieved": request_recieved.isoformat(),
    }

    ### Output Variables
    response_json = {}
    out_files = {}

    audio_blob = storage_client.get_container_client(CONFIG.input_files.audio.bucket_name).get_blob_client(
        CONFIG.input_files.audio.full_path, #version_id=CONFIG.input_files.audio.version
    )

    try: 
        ### Try to fetch blob properties with the condition that the ETag must match the desired_etag
        etag_value = audio_blob.get_blob_properties(if_match=CONFIG.input_files.audio.version)
        logging.info(f'Audio Blob Name: {audio_blob.blob_name}')
        logging.info(f'Audio Blob ETag: {etag_value["etag"]}')

    except ResourceNotFoundError:
        # Handle the case where the blob with the specified ETag is not found
        abort(404, "Media file not found on bucket")

    sas_token = generate_blob_sas(
                account_name=storage_client.account_name,
                account_key=storage_client.credential.account_key,
                container_name=CONFIG.input_files.audio.bucket_name,
                blob_name=CONFIG.input_files.audio.full_path,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(minutes=30),
    )

    audio_blob_url = audio_blob.url
    logging.info(f'Media Blob URL: {audio_blob_url}')

    ### Combine the blob URL with the SAS token to get the signed URL
    target_media_signed_url = f"{audio_blob_url}?{sas_token}"

    ### Logging the staged_media_signed_url
    logging.info(f"Target Media Signed URL: {target_media_signed_url}")
    
    # Set up DG opts
    dg_opts={"api_key":""}
    if CONFIG.function_config.asr_config.url!=None:
        print("Found_URL")
        dg_opts["api_url"] = str(CONFIG.function_config.asr_config.url)
        if CONFIG.function_config.asr_config.api_key!=None:
            print("api_key")
            dg_opts["api_key"] = str(CONFIG.function_config.asr_config.api_key) 
    else: 
        dg_opts=str(CONFIG.function_config.asr_config.api_key)
    print(dg_opts)
    
    ### Send WAV to Deepgram
    deepgram = Deepgram(dg_opts) # type: ignore
    
    ### Set up input params
    source = {'url': target_media_signed_url}
    params = {
        feature: 
            True if str(val).lower()=='true'
            else False if str(val).lower()=='false'
            else int(val) if isinstance(val,str) and is_integer(val)
            else float(val) if isinstance(val,str) and is_float(val)
            else val
            for feature, val in CONFIG.function_config.asr_config.features.items()
        } if CONFIG.function_config.asr_config.features!=None else {}
    ### print(dumps(params))
    asr_response = deepgram.transcription.sync_prerecorded(source, params) ## type: ignore
    
    ### Normalize the DG input
    normalized = normalise_deepgram(loads(dumps(asr_response)), CONFIG.function_config.transcript_config.toJson())
    del asr_response
    
    ### Upload Normalized Transcript to Stage bucket
    staging_transcript_path = (
        Path(
            CONFIG.staging_config.folder_path,
            str(CONFIG.staging_config.file_prefix) + "_" + "transcript",
        )
        .with_suffix('.json')
        .as_posix()
    )
    staging_transcript_blob = storage_client.get_container_client(CONFIG.staging_config.bucket_name).get_blob_client(
        staging_transcript_path
    )
    # staging_transcript_blob.upload_from_string(dumps(normalized),content_type='application/json')

    staging_transcript_blob.upload_blob(dumps(normalized),content_type='application/json', overwrite=True)
    if not staging_transcript_blob.exists():
        abort(500,'transcript failed to upload to staging bucket')

    out_files["transcript"] = create_outgoing_file_ref(staging_transcript_blob)
    
    ### Return with all the locations
    response_json["status"] = "success"
    response_json["staged_files"] = out_files
    # return make_response(response_json, 200)
    logging.info(f"response_json_output: {response_json}")
    return func.HttpResponse(body=dumps(response_json), status_code=200, mimetype='application/json')


def is_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
    
def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False