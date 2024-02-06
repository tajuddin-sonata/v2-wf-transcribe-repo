###############################################
#############  Sample Curl ####################
###############################################

#!/bin/bash

# Replace with your Azure Function App URL
###"https://<function-app-name>.azurewebsites.net/api/<function-key>"
function_url="https://<function-app-name>.azurewebsites.net/api/<function-key>"

# Replace with your Azure Function App key or any other authentication mechanism
api_key="<function-key>"  ###"function-app-key (master)"
set -x

curl -m 59 -X POST "$function_url" -H "x-functions-key: $api_key" -H "Content-Type: application/json" -d '{"context": {"azure_subscription": "sub-dev","azure_location": "east us","client_id": "customer1","interaction_id": "test","execution_id": "id-1234"},"input_files": {"audio":{"bucket_name": "247ai-stg-cca-customer1-audio-landing","full_path": "test.wav","version": "0x8DC18A209B13338"}},"staging_config": {"bucket_name": "247ai-stg-cca-customer1-staging","folder_path": "2024/01/19/test/20240119035220_id-1234","file_prefix": "test"},"function_config": {"signing_account": "","asr_config":{"url":"http://dev-deepgram.dg.dev.usw1.cloud.247-inc.net:8080/v2","api_key":"89954365f96e90d5a07fcacacb48bd17601ab3be","features":{"punctuate":true,"numerals":"true","multichannel":true,"diarize":true}},"transcript_config":{"channel_map": ["Caller", ["Agent","Supervisor"]]}}}'

#####################################
#################### OR #############
#!/bin/bash

# Replace with your Azure Function App URL
###"https://<function-app-name>.azurewebsites.net/api/<function-key>"
function_url="https://<function-app-name>.azurewebsites.net/api/<function-key>"

# Replace with your Azure Function App key or any other authentication mechanism
api_key="<function-key>"  ###"function-app-key (master)"
set -x

curl -m 59 -X POST "$function_url" \
-H "x-functions-key: $api_key" \
-H "Content-Type: application/json" \
-d '
{
    "context": {
        "azure_subscription": "sub-dev",
        "azure_location": "east us",
        "client_id": "customer1",
        "interaction_id": "test",
        "execution_id": "id-1234"
    },
    "input_files": {
        "audio":{
            "bucket_name": "247ai-stg-cca-customer1-audio-landing",
            "full_path": "test.wav",
            "version": "0x8DC18A209B13338"
        }
    },
    "staging_config": {
        "bucket_name": "247ai-stg-cca-customer1-staging",
        "folder_path": "2024/01/19/test/20240119035220_id-1234",
        "file_prefix": "test"
    },
    "function_config": {
        "signing_account": "",
         "asr_config":{
            "url":"http://dev-deepgram.dg.dev.usw1.cloud.247-inc.net:8080/v2",  #### remove this line
            "api_key":"89954365f96e90d5a07fcacacb48bd17601ab3be",
            "features":{
                "punctuate":true,
                "numerals":"true",
                "multichannel":true,
                "diarize":true
            }
        },
        "transcript_config":{
            "channel_map": ["Caller", ["Agent","Supervisor"]]
        } 
    }
}
'


