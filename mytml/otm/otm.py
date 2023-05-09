from mytml.utils import remove_duplicates
from mytml.diagram import Trustzone, Component, Dataflow
from mytml.otm.representation import Representation, RepresentationType, DiagramRepresentation

REPRESENTATIONS_SIZE_DEFAULT_HEIGHT = 1000
REPRESENTATIONS_SIZE_DEFAULT_WIDTH = 1000


class OTM:
    def __init__(self, project_name, project_id, provider):
        self.project_name = project_name
        self.project_id = project_id
        self.representations = []
        self.trustzones = []
        self.components = []
        self.dataflows = []
        self.threats = []
        self.mitigations = []
        self.version = "0.1.0"
        self.__provider = provider

        self.add_default_representation()

    def objects_by_type(self, type):
        if type == "trustzone":
            return self.trustzones
        if type == "component":
            return self.components
        if type == "dataflow":
            return self.dataflows

    def json(self):
        json = {
            "otmVersion": self.version,
            "project": {
                "name": self.project_name,
                "id": self.project_id
            },
            "representations": [],
            "trustZones": [],
            "components": [],
            "dataflows": []
        }

        for representation in self.representations:
            json["representations"].append(representation.json())
        for trustzone in self.trustzones:
            json["trustZones"].append(trustzone.json())
        for component in self.components:
            json["components"].append(component.json())
        for dataflow in self.dataflows:
            json["dataflows"].append(dataflow.json())
        if len(self.threats) > 0:
            json["threats"] = []
            for threat in self.threats:
                json["threats"].append(threat.json())
        if len(self.mitigations) > 0:
            json["mitigations"] = []
            for mitigation in self.mitigations:
                json["mitigations"].append(mitigation.json())

        return json

    def add_trustzone(self, id=None, name=None, type=None, source=None, properties=None):
        self.trustzones.append(Trustzone(trustzone_id=id, name=name, type=type, source=source, attributes=properties))

    def add_component(self, id, name, type, parent, parent_type, source=None,
                      attributes=None, tags=None):
        self.components.append(
            Component(component_id=id, name=name, component_type=type, parent=parent, parent_type=parent_type,
                         source=source, attributes=attributes, tags=tags))

    def add_dataflow(self, id, name, source_node, destination_node, bidirectional=None,
                     source=None, attributes=None, tags=None):
        self.dataflows.append(Dataflow(dataflow_id=id, name=name, bidirectional=bidirectional, source_node=source_node,
                                          destination_node=destination_node, source=source, attributes=attributes,
                                          tags=tags))

    def add_representation(self, id_=None, name=None, type_=None):
        self.representations.append(Representation(id_=id_, name=name, type_=type_))

    def add_diagram_representation(self, id_=None, name=None, type_=None, size=None):
        self.representations.append(DiagramRepresentation(id_=id_, name=name, type_=type_, size=size))

    def add_default_representation(self):
        if not self.__provider.provider_type == RepresentationType.DIAGRAM:
            self.add_representation(id_=self.__provider.provider_name,
                                    name=self.__provider.provider_name,
                                    type_=self.__provider.provider_type)
        elif not self.representations:
            default_size = {"width": REPRESENTATIONS_SIZE_DEFAULT_WIDTH, "height": REPRESENTATIONS_SIZE_DEFAULT_HEIGHT}
            self.add_diagram_representation(id_=self.__provider.provider_name,
                                            name=self.__provider.provider_name,
                                            type_=self.__provider.provider_type,
                                            size=default_size)



class OTMBuilder:

    def __init__(self, project_id: str, project_name: str, provider):
        self.project_id = project_id
        self.project_name = project_name
        self.provider = provider

        self.__init_otm()

    def build(self):
        return self.otm

    def add_default_trustzone(self, default_trustzone):
        self.add_trustzones([default_trustzone])
        return self

    def add_trustzones(self, trustzones):
        self.otm.trustzones = remove_duplicates(self.otm.trustzones + trustzones)
        return self

    def add_components(self, components):
        self.otm.components = components
        return self

    def add_dataflows(self, dataflows):
        self.otm.dataflows = dataflows
        return self

    def add_representations(self, representations, extend: bool = True):
        if extend:
            self.otm.representations.extend(representations)
        else:
            self.otm.representations = representations

        return self

    def add_threats(self, threats):
        self.otm.threats = threats
        return self

    def add_mitigations(self, mitigations):
        self.otm.mitigations = mitigations
        return self

    def __init_otm(self):
        self.otm = OTM(self.project_name, self.project_id, self.provider)



class OTMPruner:

    def __init__(self, otm):
        self.otm = otm
        self.otm_component_ids = [c.id for c in self.otm.components]

    def prune_orphan_dataflows(self):
        dataflows = []
        for df in self.otm.dataflows:
            if df.source_node in self.otm_component_ids and df.destination_node in self.otm_component_ids:
                dataflows.append(df)
            else:
                # logger.warning(f'The dataflow {df} has been removed because connects an element that is not a '
                #                f'component'
                # )
                pass
        self.otm.dataflows = dataflows




PERMIT_ANY_REPRESENTATIONS_VOID = False


class OTMRepresentationsPruner:

    def __init__(self, otm: OTM):
        self.otm: OTM = otm

    def prune(self):
        if PERMIT_ANY_REPRESENTATIONS_VOID:
            return

        any_representation_empty = self.is_any_representation_empty()

        if any_representation_empty:
            self.remove_all_representations()

    def is_any_representation_empty(self):

        if not self.otm.representations:
            return True

        for trustzone in self.otm.trustzones:
            if not trustzone.representations:
                return True

        for component in self.otm.components:
            if not component.representations:
                return True

        return False

    def remove_all_representations(self):
        for trustzone in self.otm.trustzones:
            trustzone.representations = None

        for component in self.otm.components:
            component.representations = None



class OTMTrustZoneUnifier:

    def __init__(self, otm: OTM):
        self.otm: OTM = otm

    def unify(self):

        for tz in self.otm.trustzones:
            valid_id = tz.type
            old_id = tz.id
            self.change_childs(old_id, valid_id)
            tz.id = valid_id

        self.delete_duplicated_tz()

    def change_childs(self, old_id, valid_id):
        for child in self.otm.components + self.otm.trustzones:
            if child.parent == old_id:
                child.parent = valid_id

    def delete_duplicated_tz(self):
        deduplicated = dict()
        for tz in self.otm.trustzones:
            id_ = tz.id
            if id_ not in deduplicated:
                deduplicated[id_] = tz
        self.otm.trustzones = [v for k, v in deduplicated.items()]


