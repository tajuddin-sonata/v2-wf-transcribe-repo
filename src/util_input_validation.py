

# JSONSchema for Request Body validation
schema = {
    "type": "object",
    "properties": {
        "context": {
            "type": "object",
            "properties": {
                "azure_subscription": {"type": "string"},
                "azure_location": {"type": "string"},
                "client_id": {"type": "string"},
                "interaction_id": {"type": "string"},
                "execution_id": {"type": "string"},
            },
            "required": ["azure_subscription", "azure_location", "client_id", "interaction_id","execution_id"],
        },
        "input_files": {
            "type": "object",
            "properties": {
                "audio": {"$ref": "#/$defs/file"},
            },
            "required":["audio"]
        },
        "staging_config": {
            "type": "object",
            "properties": {
                "bucket_name": {"type": "string"},
                "folder_path": {"type": "string"},
                "file_prefix": {"type": "string"},
            },
            "required": [
                "bucket_name",
                "folder_path",
                "file_prefix",
            ],
        },
        "function_config": {
            "type": "object",
            "properties": {
                "signing_account":{"type":"string"},
                "asr_config": {
                    "type": "object",
                    "anyOf": [
                        {
                            "properties": {
                                "features": {
                                    "type": "object",
                                    "patternProperties": {
                                        ".*": {"type": ["string", "boolean"]}
                                    },
                                },
                                # "keywords": {"type": "array", "items": {"type": "string"}},
                                "url": {"type": "string"},
                                "api_key": {"type": "string"},
                            },
                            "required": ["url"],
                        },
                        {
                            "properties": {
                                "features": {
                                    "type": "object",
                                    "patternProperties": {
                                        ".*": {"type": ["string", "boolean"]}
                                    },
                                },
                                # "keywords": {"type": "array", "items": {"type": "string"}},
                                "url": {"type": "string"},
                                "api_key": {"type": "string"},
                            },
                            "required": ["api_key"],
                        },
                    ],
                },
                "transcript_config": {
                    "type": "object",
                    "properties": {
                        "channel_map": {"type": "array", "items": {"type": ["string", "array"]}}
                    },
                    "required": ["channel_map"],
                },
            },
            "required": ["signing_account","asr_config","transcript_config"],
        },
    },
    "required": ["context", "input_files", "staging_config", "function_config"],
    "$defs": {
        "file": {
            "type": "object",
            "properties": {
                "bucket_name": {"type": "string"},
                "full_path": {"type": "string"},
                "version": {"type": "string"},
                "size": {"type": "string"},
                "content_type": {"type": "string"},
                "uploaded": {"type": "string"},
            },
            "required": ["bucket_name", "full_path", "version"],
        }
    },
}

from datetime import datetime
from typing import Union
from ciso8601 import parse_datetime
from json import dumps, loads
# from jsonschema import validate, ValidationError


def jsonify(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj.__dict__


class Jsonable(object):
    def __repr__(self):
        return dumps(self, default=jsonify, indent=4)

    def toJson(self):
        return loads(repr(self))

    def __contains__(self, attr):
        return attr in self.__dict__

    def __getitem__(self, attr):
        return self.__dict__[attr]

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()

# class Config(Jsonable):
#     def __init__(self, req):
#         try:
#             validate(req, schema)  # Validate against the defined schema
#             self.context = self.Context(req["context"])
#             self.input_files = self.InputFiles(req["input_files"])
#             self.staging_config = self.StagingConfig(req["staging_config"])
#             self.function_config = self.FunctionConfig(req["function_config"])
#         except ValidationError as e:
#             raise ValueError(f"Invalid request format: {e}")


class Config(Jsonable):
    def __init__(self, req):
        self.context = self.Context(req["context"])
        self.input_files = self.InputFiles(req["input_files"])
        self.staging_config = self.StagingConfig(req["staging_config"])
        self.function_config = self.FunctionConfig(req["function_config"]) 

    class Context(Jsonable):
        def __init__(self, c):
            self.azure_subscription = str(c["azure_subscription"]) if "azure_subscription" in c else None
            self.azure_location = str(c["azure_location"]) if "azure_location" in c else None
            self.client_id = str(c["client_id"])
            self.interaction_id = str(c["interaction_id"]) if "interaction_id" in c else None
            self.execution_id = str(c["execution_id"]) if "execution_id" in c else None
            # self.execution_id = str(c.get("execution_id", ""))

    class InputFiles(Jsonable):
        def __init__(self, c):
            self.audio=self.InputFile(c["audio"])
        
        class InputFile(Jsonable):
            def __init__(self, c):
                self.bucket_name = str(c["bucket_name"])
                self.full_path = str(c["full_path"])
                # self.version = int(c["version"])
                self.version = str(c["version"])
                self.size = int(c["size"]) if "size" in c else None
                self.content_type = (
                    str(c["content_type"]) if "content_type" in c else None
                )
                self.uploaded = (
                    parse_datetime(str(c["uploaded"])) if "uploaded" in c else None
                )

    class StagingConfig(Jsonable):
        def __init__(self, c):
            self.bucket_name = str(c["bucket_name"])
            self.folder_path = str(c["folder_path"])
            self.file_prefix = str(c["file_prefix"])

    class FunctionConfig(Jsonable):
        def __init__(self, c):
            self.signing_account = str(c["signing_account"])
            self.asr_config = self.ASRConfig(c["asr_config"])
            self.transcript_config = self.TranscriptConfig(c["transcript_config"])

        class ASRConfig(Jsonable):
            def __init__(self, c):
                self.features: Union[dict[str,Union[int,float,str,bool,list[str]]],None] = c["features"] if "features" in c else None
                self.url = str(c["url"]) if "url" in c else None
                self.api_key = str(c["api_key"]) if "api_key" in c else None
                
        class TranscriptConfig(Jsonable):
            def __init__(self, c):
                self.channel_map: list[Union[str,list[str]]] = c["channel_map"]
                

