from mytml.otm.representation import DiagramRepresentation, RepresentationType
from mytml.otm.representation_calculator import build_size_object, calculate_diagram_size, RepresentationCalculator
from mytml.otm.diagram_mapper import DiagramComponentMapper, DiagramConnectorMapper, DiagramTrustzoneMapper
from mytml.diagram import DiagramPruner
from mytml.otm.otm import OTMBuilder, OTMPruner

class VisioParser:
    def __init__(self, project_id: str, project_name: str, diagram, mapping_loader):
        self.project_id = project_id
        self.project_name = project_name
        self.diagram = diagram
        self.mapping_loader = mapping_loader

        self.representation_id = f'{self.project_id}-diagram'
        self.representations = [
            DiagramRepresentation(
                id_=self.representation_id,
                name=f'{self.project_id} Diagram Representation',
                type_=RepresentationType.DIAGRAM,
                size=build_size_object(calculate_diagram_size(self.diagram.limits))
            )
        ]

        self._representation_calculator = RepresentationCalculator(self.representation_id, self.diagram.limits)
        self._trustzone_mappings = self.mapping_loader.get_trustzone_mappings()
        self._component_mappings = self.mapping_loader.get_component_mappings()
        self.__default_trustzone = self.mapping_loader.get_default_otm_trustzone()


    def build_otm(self):
        self.__prune_diagram()

        components = self.__map_components()
        trustzones = self.__map_trustzones()
        dataflows = self.__map_dataflows()

        otm = self.__build_otm(trustzones, components, dataflows)

        OTMPruner(otm).prune_orphan_dataflows()

        return otm

    def __prune_diagram(self):
        DiagramPruner(self.diagram, self.mapping_loader.get_all_labels()).run()

    def __map_trustzones(self):
        trustzone_mapper = DiagramTrustzoneMapper(
            self.diagram.components,
            self._trustzone_mappings,
            self._representation_calculator
        )
        return trustzone_mapper.to_otm()

    def __map_components(self):
        return DiagramComponentMapper(
            self.diagram.components,
            self._component_mappings,
            self._trustzone_mappings,
            self.__default_trustzone,
            self._representation_calculator,
        ).to_otm()

    def __map_dataflows(self):
        return DiagramConnectorMapper(self.diagram.connectors).to_otm()

    def __build_otm(self, trustzones, components, dataflows):
        otm_builder = OTMBuilder(self.project_id, self.project_name, self.diagram.diagram_type) \
            .add_representations(self.representations, extend=False) \
            .add_trustzones(trustzones) \
            .add_components(components) \
            .add_dataflows(dataflows)

        if self.__default_trustzone and self.__any_default_tz(components):
            otm_builder.add_default_trustzone(self.__default_trustzone)

        return otm_builder.build()

    def __any_default_tz(self, components):
        for component in components:
            if self.__default_trustzone and component.parent \
                    and component.parent == self.__default_trustzone.id:
                return True
        return False

