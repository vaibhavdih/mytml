from mytml.diagram import DiagramComponent, DiagramConnector
from mytml.utils import normalize_label, get_shape_text, get_master_shape_text, get_unique_id_text

class VisioComponentFactory:
    def create_component(self, shape, origin, representer):
        return DiagramComponent(id = shape.ID, name=normalize_label(get_shape_text(shape)), type = normalize_label(get_master_shape_text(shape)), origin = origin , representation = representer.build_representation(shape), unique_id = get_unique_id_text(shape))

class VisioConnectorFactory:

    @staticmethod
    def _is_valid_connector(connected_shapes):
        if len(connected_shapes) < 2:
            return False
        if connected_shapes[0].shape_id == connected_shapes[1].shape_id:
            return False
        return True

    @staticmethod
    def _is_bidirectional_connector(shape):
        if shape.master_page.name is not None and "Double Arrow" in shape.master_page.name:
            return True
        for arrow_value in [shape.cell_value(att) for att in ["BeginArrow", "EndArrow"]]:
            if (
                arrow_value is None
                or not str(arrow_value).isnumeric()
                or arrow_value == "0"
            ):
                return False
        return True

    @staticmethod
    def _is_created_from(connector):
        return connector.from_rel == "BeginX"

    @staticmethod
    def _connector_has_arrow_in_origin(shape):
        begin_arrow_value = shape.cell_value("BeginArrow")
        return (
            begin_arrow_value is not None
            and str(begin_arrow_value).isnumeric()
            and begin_arrow_value != "0"
        )


    def create_connector(self, shape):
        connected_shapes = shape.connects
        if not self._is_valid_connector(connected_shapes):
            return None

        if self._is_bidirectional_connector(shape):
            return DiagramConnector(
                shape.ID,
                connected_shapes[0].shape_id,
                connected_shapes[1].shape_id,
                True,
            )

        has_arrow_in_origin = self._connector_has_arrow_in_origin(shape)

        if (not has_arrow_in_origin and self._is_created_from(connected_shapes[0])) or (
            has_arrow_in_origin and self._is_created_from(connected_shapes[1])
        ):
            return DiagramConnector(
                shape.ID, connected_shapes[0].shape_id, connected_shapes[1].shape_id
            )
        else:
            return DiagramConnector(
                shape.ID, connected_shapes[1].shape_id, connected_shapes[0].shape_id
            )
