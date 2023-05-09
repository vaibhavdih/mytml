from shapely.geometry import Polygon
from vsdx import Shape
from mytml.utils import get_limits


class SimpleComponentRepresenter:

    def build_representation(self, shape: Shape) -> Polygon:
        limits = get_limits(shape)

        points = [(limits[0][0], limits[0][1]),
                  (limits[0][0], limits[1][1]),
                  (limits[1][0], limits[1][1]),
                  (limits[1][0], limits[0][1])]

        return Polygon(points)
