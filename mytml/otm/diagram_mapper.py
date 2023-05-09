
from mytml.utils import normalize_label , deterministic_uuid
from mytml.diagram import Component, Dataflow, Trustzone
from enum import Enum 


class ParentType(Enum):
    TRUST_ZONE = 'trustZone'
    COMPONENT = 'component'

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)


class DiagramComponentMapper:

    def __init__(self,
                 components,
                 component_mappings: dict,
                 trustzone_mappings: dict,
                 default_trustzone,
                 representation_calculator):
        self.components = components
        self.normalized_component_mappings = {normalize_label(lb): value for (lb, value) in component_mappings.items()}
        self.trustzone_mappings = trustzone_mappings
        self.default_trustzone = default_trustzone

        self.representation_calculator = representation_calculator

    def _calculate_parent_type(self, component):
        if not component.parent or component.parent.name in self._get_trustzone_mappings().keys():
            return ParentType.TRUST_ZONE
        else:
            return ParentType.COMPONENT

    def to_otm(self):
        return self.__map_to_otm(self.__filter_components())

    def __filter_components(self):
        return [component for component in self.components if self.__filter_component(component)]

    def __filter_component(self, component):
        map_by_name = normalize_label(component.name) in self.normalized_component_mappings
        map_by_type = normalize_label(component.type) in self.normalized_component_mappings
        map_by_unique_id = component.unique_id in self.normalized_component_mappings
        return map_by_name or map_by_type or map_by_unique_id

    def __map_to_otm(self, component_candidates):
        return list(map(self.__build_otm_component, component_candidates))

    def __build_otm_component(self, diagram_component):
        representation = self.representation_calculator.calculate_representation(diagram_component)

        return Component(
            component_id=diagram_component.id,
            name=diagram_component.name,
            component_type=self.__calculate_otm_type(diagram_component.name,
                                                     diagram_component.type,
                                                     diagram_component.unique_id),
            parent=self.__calculate_parent_id(diagram_component),
            parent_type=self._calculate_parent_type(diagram_component),
            representations=[representation] if representation else None
        )

    def __calculate_otm_type(self, component_name: str, component_type: str, component_unique_id: str) -> str:
        otm_type = self.__find_mapped_component_by_label(component_unique_id)

        if not otm_type:
            otm_type = self.__find_mapped_component_by_label(component_name)

        if not otm_type:
            otm_type = self.__find_mapped_component_by_label(component_type)

        return otm_type or 'empty-component'

    def __find_mapped_component_by_label(self, label: str) -> str:
        return self.normalized_component_mappings[normalize_label(label)]['type'] \
            if normalize_label(label) in self.normalized_component_mappings else None

    def __calculate_parent_id(self, component) -> str:
        if component.parent:
            return component.parent.id

        if self.default_trustzone:
            return self.default_trustzone.id

        raise Exception('Mapping files are not valid No default trust zone has been defined in the mapping file Please, add a default trust zone')

    def _get_trustzone_mappings(self):
        return self.trustzone_mappings




class DiagramConnectorMapper:
    def __init__ (self, connectors):
        self.connectors = connectors

    @staticmethod
    def build_otm_dataflow(diagram_connector):
        return Dataflow(
            dataflow_id=diagram_connector.id,
            name=diagram_connector.name if diagram_connector.name else deterministic_uuid(diagram_connector.id),
            source_node=diagram_connector.from_id,
            destination_node=diagram_connector.to_id,
            bidirectional=diagram_connector.bidirectional if diagram_connector.bidirectional else None
        )

    def to_otm(self):
        return list(map(self.build_otm_dataflow, self.connectors))




class DiagramTrustzoneMapper:

    def __init__(self,
                 components,
                 trustzone_mappings: dict,
                 representation_calculator):
        self.components = components
        self.trustzone_mappings = trustzone_mappings
        self.representation_calculator = representation_calculator

    def to_otm(self):
        return self.__map_to_otm(self.__filter_trustzones())

    def __filter_trustzones(self):
        trustzones = []

        for c in self.components:
            if c.name in self.trustzone_mappings:
                c.trustzone = True
                trustzones.append(c)

        return trustzones

    def __map_to_otm(self, trustzones):
        return list(map(self.__build_otm_trustzone, trustzones)) \
            if trustzones \
            else []

    def __build_otm_trustzone(self, trustzone):
        trustzone_mapping = self.trustzone_mappings[trustzone.name]

        representation = self.representation_calculator.calculate_representation(trustzone)
        return Trustzone(
            trustzone_id=trustzone.id,
            name=trustzone.name if trustzone.name else trustzone_mapping['type'],
            parent=self.__calculate_parent_id(trustzone),
            parent_type=self._calculate_parent_type(trustzone),
            type=self.find_type(trustzone_mapping),
            representations=[representation] if representation else None
        )

    @staticmethod
    def find_type(trustzone_mapping):
        if 'id' in trustzone_mapping:
            return trustzone_mapping['id']
        return trustzone_mapping['type']


    def __calculate_parent_id(self, component):
        if component.parent:
            return component.parent.id

    def _calculate_parent_type(self, component):
        if not component.parent or component.parent.name in self._get_trustzone_mappings().keys():
            return ParentType.TRUST_ZONE
        else:
            return ParentType.COMPONENT

    def _get_trustzone_mappings(self):
        return self.trustzone_mappings
