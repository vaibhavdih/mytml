from vsdx import VisioFile
from mytml.diagram import Diagram, DiagramLimits, DiagramComponentOrigin
from mytml.utils import get_limits, get_shape_text
from mytml.parent_calculator import ParentCalculator
from mytml.representation.simple_component_representer import SimpleComponentRepresenter
from mytml.representation.zone_component_representer import ZoneComponentRepresenter


DIAGRAM_LIMITS_PADDING = 2
DEFAULT_DIAGRAM_LIMITS = DiagramLimits(((1000, 1000), (1000, 1000)))


class VsdxParser:
    def __init__(self, component_factory, connector_factory):
        self.component_factory = component_factory
        self.connector_factory = connector_factory

        self._zone_representer = None
        self._component_representer = None

        self.page = None
        self._visio_components = []
        self._visio_connectors = []

    @staticmethod
    def _load_visio_page_from_file(diagram_filename):
        with VisioFile(diagram_filename) as f:
            return f.pages[0]

    def parse(self, diagram_filename):
        self.page = self._load_visio_page_from_file(diagram_filename)

        diagram_limits = self._calculate_diagram_limits()
        self._component_representer = SimpleComponentRepresenter()
        self._zone_representer = ZoneComponentRepresenter(diagram_limits)
        self._load_page_elements()
        self._calculate_parents()

        return Diagram(self._visio_components, self._visio_connectors, diagram_limits)

    @staticmethod
    def _is_connector(shape):
        for connect in shape.connects:
            if shape.ID == connect.connector_shape_id:
                return True
        return False

    @staticmethod
    def _is_boundary(shape):
        return shape.shape_name is not None and "Curved panel" in shape.shape_name

    def _is_component(self, shape):
        return get_shape_text(shape) and not self._is_connector(shape)

    def _calculate_diagram_limits(self):
        floor_coordinates = [None, None]
        top_coordinates = [0, 0]

        for shape_limits in map(get_limits, self.page.child_shapes):
            if not floor_coordinates[0] or shape_limits[0][0] < floor_coordinates[0]:
                floor_coordinates[0] = shape_limits[0][0] - DIAGRAM_LIMITS_PADDING

            if not floor_coordinates[1] or shape_limits[0][1] < floor_coordinates[1]:
                floor_coordinates[1] = shape_limits[0][1] - DIAGRAM_LIMITS_PADDING

            if shape_limits[1][0] > top_coordinates[0]:
                top_coordinates[0] = shape_limits[1][0] + DIAGRAM_LIMITS_PADDING

            if shape_limits[1][1] > top_coordinates[1]:
                top_coordinates[1] = shape_limits[1][1] + DIAGRAM_LIMITS_PADDING

        return (
            DiagramLimits([floor_coordinates, top_coordinates])
            if floor_coordinates[0] and floor_coordinates[1]
            else DEFAULT_DIAGRAM_LIMITS
        )

    def _load_page_elements(self):
        for shape in self.page.child_shapes:
            if self._is_connector(shape):
                self._add_connector(shape)
            elif self._is_boundary(shape):
                self._add_boundary_component(shape)
            elif self._is_component(shape):
                self._add_simple_component(shape)

    def _add_simple_component(self, component_shape):
        self._visio_components.append(
            self.component_factory.create_component(
                component_shape, DiagramComponentOrigin.SIMPLE_COMPONENT, self._component_representer
            )
        )

    def _add_boundary_component(self, component_shape):
        self._visio_components.append(
            self.component_factory.create_component(
                component_shape, DiagramComponentOrigin.BOUNDARY, self._zone_representer
            )
        )

    def _add_connector(self, connector_shape):
        visio_connector = self.connector_factory.create_connector(connector_shape)
        if visio_connector:
            self._visio_connectors.append(visio_connector)

    def _calculate_parents(self):
        for component in self._visio_components:
            component.parent = ParentCalculator(component).calculate_parent(
                self._visio_components
            )
