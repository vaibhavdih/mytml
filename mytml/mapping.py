from abc import ABCMeta
import os
import yaml
import json 
import jmespath
import jsonschema
import pkg_resources
from deepmerge import always_merger
from mytml.utils import normalize_unique_id, deterministic_uuid
from mytml.diagram import Trustzone

MAX_SIZE = 5 * 1024 * 1024 
MIN_SIZE = 5

PUBLIC_CLOUD_NAME = 'Public Cloud'
PUBLIC_CLOUD = Trustzone(trustzone_id=deterministic_uuid(PUBLIC_CLOUD_NAME), name=PUBLIC_CLOUD_NAME,
                         type='b61d6911-338d-46a8-9f39-8dcd24abfe91', attributes={"default": True})



# functions of validation

def validate_size(mapping_file_data):
    size = len(mapping_file_data)
    if size > MAX_SIZE or size < MIN_SIZE:
        msg = 'Mapping files are not valid. Invalid size'
        raise Exception(msg)


def validate_type(mapping_file_data):
    try:
        if isinstance(mapping_file_data, bytes):
            mapping_file_data.decode()
    except Exception:
        msg = 'The mapping file cannot read as plain text'
        raise Exception(msg)


def validate_schema(mapping_file):
    schema = Schema()
    schema.validate(read_mapping_file(mapping_file))
    if not schema.valid:
        raise Exception('Mapping files are not valid')


def read_mapping_file(mapping_file: bytes):
    try:
        return yaml.load(mapping_file, Loader=yaml.SafeLoader)
    except Exception as e:
        raise Exception('Error reading the mapping file. The mapping files are not valid.')


def validate_mapping_file(mapping_file):
    validate_size(mapping_file)
    validate_type(mapping_file)
    validate_schema(mapping_file)



class Schema:
    def __init__(self):
        self.schema_file = self.__load_schema("mytml/data/diagram_mapping_schema.json")
        self.errors = ""
        self.valid = None

    def validate(self, document):
        try:
            jsonschema.validate(document, self.schema_file)
            self.valid = True
        except jsonschema.SchemaError as e:
            self.errors = e.message
            self.valid = False
        except jsonschema.ValidationError as e:
            self.errors = e.message
            self.valid = False

    def json(self):
        return json.dumps(self.schema_file, indent=2)

    def __load_schema(self, schema_path):
        with open(schema_path, "r") as f:
            return yaml.load(f, Loader=yaml.BaseLoader)

    @staticmethod
    def from_package(package: str, filename: str):
        schema_path = pkg_resources.resource_filename(package, os.path.join('resources/schemas', filename))
        return Schema(schema_path)



class MappingFileLoader(metaclass = ABCMeta):
    def __init__(self, mapping_files_data):
        self.mapping_files = mapping_files_data
        self.map = {}

    def load(self):
        if not self.mapping_files:
            msg = "Mapping File is empty"
            raise Exception(msg)
        
        validate_size(self.mapping_files[0])

        try:
            for mapping_file_data in self.mapping_files:
                if not mapping_file_data:
                    continue 
                data = mapping_file_data if isinstance(mapping_file_data, str) else mapping_file_data.decode()
                self._load(yaml.load(data, Loader=yaml.BaseLoader))
        except Exception as e:
            raise Exception(f"Error loading the mapping file {e.__class__.__name__} {str(e)}")
        return self.map

    def get_mappings(self):
        return self.map 

    def _load(self, mapping):
        always_merger.merge(self.map, mapping)



class MainMappingFileLoader:

    def __init__(self, mapping_files):
        self.component_mappings = None
        self.trustzone_mappings = None 
        self.default_otm_trustzone = None 
        mapping = MappingFileLoader(mapping_files).load()
        self.mappings = self._load_mappings(mapping)

    @staticmethod
    def _load_mappings(mapping_file):
        if isinstance(mapping_file, dict):
            return mapping_file
        else:
            if isinstance(mapping_file, str):
                with open(mapping_file, 'r') as f:
                    return always_merger.merge(mapping_file, yaml.safe_load(f))
            else:
                return always_merger.merge(mapping_file, yaml.safe_load(mapping_file))

    def load(self):
        self.default_otm_trustzone = self.__load_default_otm_trustzone()
        self.trustzone_mappings = self.__load_trustzone_mappings()
        self.component_mappings = self.__load_component_mappings()

    def get_all_labels(self):
        component_and_tz_mappings = self.mappings['components'] + self.mappings['trustzones']
        return [c['label'] for c in component_and_tz_mappings]

    def __load_default_otm_trustzone(self):
        trustzone_mappings_list = jmespath.search("trustzones", self.mappings)
        default_trustzones = [v for v in trustzone_mappings_list if 'default' in v and v['default']]
        default_otm_trustzone = default_trustzones[-1] if len(default_trustzones) > 0 else None
        if default_otm_trustzone:
            name = default_otm_trustzone['label']
            return Trustzone(trustzone_id=deterministic_uuid(name), name=name, type=default_otm_trustzone['type'],
                             attributes={"default": True})
        else:
            return PUBLIC_CLOUD

    def __load_trustzone_mappings(self):
        trustzone_mappings_list = jmespath.search("trustzones", self.mappings)
        return dict(zip([tz['label'] for tz in trustzone_mappings_list], trustzone_mappings_list))

    def __load_component_mappings(self):
        component_mappings_list = jmespath.search("components", self.mappings)
        return dict(zip([self.__get_component_identifier(cp) for cp in component_mappings_list],
                        component_mappings_list))

    def __get_component_identifier(self, component: dict) -> str:
        identifier = component.get('id', component['label'])
        return normalize_unique_id(identifier)

    def get_trustzone_mappings(self):
        return self.trustzone_mappings

    def get_default_otm_trustzone(self):
        return self.default_otm_trustzone

    def get_component_mappings(self):
        return self.component_mappings




class MappingFileValidator:
    def __init__(self, mapping_file):
        self.mapping_file = mapping_file 

    def validate(self):
        validate_mapping_file( self.mapping_file)


class MultipleMappingFileValidator:
    def __init__(self, mapping_files):
        self.mapping_files = mapping_files

    def validate(self):
        for mapping_file in self.mapping_files:
            validate_mapping_file(mapping_file)


