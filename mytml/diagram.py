from shapely.geometry import Polygon
from enum import Enum
from mytml.utils import normalize_label, remove_from_list


class RepresentationType(Enum):
    DIAGRAM = 'diagram'
    CODE = 'code'
    THREAT_MODEL = 'threat-model'


class DiagramComponentOrigin(Enum):
    SIMPLE_COMPONENT = 1
    BOUNDARY = 2



class Provider(Enum):

    def __new__(cls, value, provider_name: str, provider_type, valid_mime):
        obj = str.__new__(cls, [value])
        obj._value_ = value
        obj.provider_name = provider_name
        obj.provider_type = provider_type
        obj.valid_mime = valid_mime

        return obj



class DiagramType(str, Provider):
    VISIO = ("VISIO", "Visio", RepresentationType.DIAGRAM,
             ['application/vnd.ms-visio.drawing.main+xml', 'application/octet-stream'])
    


class DiagramComponent:
    def __init__(
        self,
        id=None,
        name=None,
        type=None,
        origin=None,
        parent=None,
        trustzone=False,
        representation=None,
        unique_id=None,
    ):
        self.id = id
        self.name = name
        self.type = type
        self.origin = origin
        self.parent = parent
        self.trustzone = trustzone
        self.representation = representation
        self.unique_id = unique_id

    def get_component_category(self):
        return "trustZone" if not self.parent else "component"


class DiagramConnector:
    def __init__(self, id, from_id, to_id, bidirectional=False, name=None):
        self.id = id
        self.from_id = from_id
        self.to_id = to_id
        self.bidirectional = bidirectional
        self.name = name


class DiagramLimits:
    def __init__(self, limits):
        self.x_floor = limits[0][0]
        self.y_floor = limits[0][1]
        self.x_top = limits[1][0]
        self.y_top = limits[1][1]


class Diagram:
    def __init__(self, components, connectors, limits=None):
        self.diagram_type = DiagramType.VISIO
        self.components = components
        self.connectors = connectors
        self.limits = limits



class DiagramPruner:

    def __init__(self, diagram: Diagram, mapped_labels: [str]):
        self.components = diagram.components
        self.connectors = diagram.connectors
        self.normalized_mapped_labels = [normalize_label(mapped_label) for mapped_label in mapped_labels]

        self.__removed_components = []

    def run(self):
        self.__remove_unmapped_components()
        self.__prune_orphan_connectors()
        self.__restore_parents()

    def __remove_unmapped_components(self):
        remove_from_list(
            self.components,
            lambda component: not self.__is_component_mapped(component),
            self.__remove_component
        )

    def __prune_orphan_connectors(self):
        removed_components_ids = [removed_component.id for removed_component in self.__removed_components]
        remove_from_list(
            self.connectors,
            lambda connector: connector.from_id in removed_components_ids or connector.to_id in removed_components_ids
        )

    def __restore_parents(self):
        self.__squash_removed_components()

        removed_parents = dict(zip(
            [dc.id for dc in self.__removed_components], [dc.parent for dc in self.__removed_components]))

        for diagram_component in self.components:
            if diagram_component.parent and diagram_component.parent.id in removed_parents:
                diagram_component.parent = removed_parents[diagram_component.parent.id]

    def __is_component_mapped(self, component: DiagramComponent):
        map_by_name = normalize_label(component.name) in self.normalized_mapped_labels
        map_by_type = normalize_label(component.type) in self.normalized_mapped_labels

        return map_by_name or map_by_type

    def __remove_component(self, component: DiagramComponent):
        self.components.remove(component)
        self.__store_removed_component(component)

    def __store_removed_component(self, component: DiagramComponent):
        self.__removed_components.append(component)

    def __squash_removed_components(self):
        for removed_component in self.__removed_components:
            removed_component.parent = self.__find_alive_parent(removed_component)

    def __find_alive_parent(self, component: DiagramComponent):
        if component.parent is None:
            return None

        if component.parent not in self.__removed_components:
            return component.parent

        self.__find_alive_parent(component.parent)


#########################################3333
# otm components

class Trustzone:
    def __init__(self, trustzone_id, name, parent=None, parent_type = None, source=None, type=type, attributes=None, representations=None):
        self.id = trustzone_id
        self.name = name
        self.type = type
        self.parent = parent
        self.parent_type = parent_type
        self.source = source
        self.attributes = attributes
        self.trustrating = 10
        self.representations = representations

    def __eq__(self, other):
        return type(other) == Trustzone and self.id == other.id

    def __repr__(self) -> str:
        return f'Trustzone(id="{self.id}", name="{self.name}", type="{self.type}", source="{self.source}", ' \
               f'attributes="{self.attributes}, trustrating="{self.trustrating}")'

    def __hash__(self):
        return hash(self.__repr__())

    def json(self):
        json = {
            "id": self.id,
            "name": self.name,
            "risk": {
                "trustRating": self.trustrating
            }
        }
        if self.parent and self.parent_type:
            json["parent"] = {
                str(self.parent_type): self.parent
            }
        if self.attributes:
            json["attributes"] = self.attributes
        if self.representations:
            json["representations"] = [r.json() for r in self.representations]

        return json



class Component:
    def __init__(self, component_id, name, component_type, parent, parent_type, source=None,
                 attributes=None, tags=None, threats = None, representations=None):
        self.id = component_id
        self.name = name
        self.type = component_type
        self.parent = parent
        self.parent_type = parent_type
        self.source = source
        self.attributes = attributes
        self.tags = tags
        self.threats = threats or []
        self.representations = representations

    def add_threat(self, threat):
        self.threats.append(threat)

    def json(self):
        json = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "parent": {
                str(self.parent_type): self.parent
            }
        }

        if self.attributes:
            json["attributes"] = self.attributes
        if self.tags:
            json["tags"] = self.tags
        if self.representations:
            json["representations"] = [r.json() for r in self.representations]

        if len(self.threats) > 0:
            json["threats"] = []
            for threat in self.threats:
                json["threats"].append(threat.json())

        return json


class Dataflow:
    def __init__(self, dataflow_id, name, source_node, destination_node, bidirectional: bool = None,
                 source=None, attributes=None, tags=None):
        self.id = dataflow_id
        self.name = name
        self.bidirectional = bidirectional
        self.source_node = source_node
        self.destination_node = destination_node
        self.source = source
        self.attributes = attributes
        self.tags = tags

    def json(self):
        json = {
            "id": self.id,
            "name": self.name,
            "source": self.source_node,
            "destination": self.destination_node
        }

        if self.bidirectional is not None:
            json["bidirectional"] = self.bidirectional
        if self.attributes:
            json["attributes"] = self.attributes
        if self.tags:
            json["tags"] = self.tags

        return json

    def __repr__(self):
        return f'Dataflow(id="{self.id}", name="{self.name}", source="{self.source_node}", ' \
               f'destination="{self.destination_node}")'

