from mytml.validator import Validator
from mytml.loader import Loader
from mytml.mapping import MultipleMappingFileValidator, MainMappingFileLoader
from mytml.visio_parser import VisioParser
from mytml.otm.otm import OTMRepresentationsPruner, OTMTrustZoneUnifier

class Processor:
    def __init__(self, project_id, source, mappings):
        self.project_id = project_id
        self.project_name = project_id
        self.source = source
        self.mappings = mappings

        self.loader = None
        self.mapping_loader = None

    def process(self):
        Validator(self.source).validate()

        self.loader = Loader(self.source)
        self.loader.load()

        mapping_validator = MultipleMappingFileValidator(self.mappings).validate()
        self.mapping_loader = MainMappingFileLoader(self.mappings)
        self.mapping_loader.load()

        visio = self.loader.get_visio()
        otm = VisioParser(self.project_id, self.project_name, visio, self.mapping_loader).build_otm()

        OTMRepresentationsPruner(otm).prune()
        OTMTrustZoneUnifier(otm).unify()

        # validate otm function
        return otm