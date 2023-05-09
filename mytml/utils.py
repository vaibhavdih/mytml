import re
from math import pi
import random
import uuid
from vsdx import Shape


def get_shape_text(shape: Shape) -> str:
    result = shape.text
    if not result:
        result = get_child_shapes_text(shape.child_shapes)

    if not result:
        result = get_master_shape_text(shape)

    return (result or "").strip()


def get_master_shape_text(shape: Shape) -> str:
    if not shape.master_shape:
        return ""

    result = shape.master_shape.text
    if not result:
        result = get_child_shapes_text(shape.master_shape.child_shapes)

    return (result or "").strip()


def get_unique_id_text(shape: Shape) -> str:
    if not shape.master_page or not shape.master_page.master_unique_id:
        return ""

    unique_id = shape.master_page.master_unique_id.strip()
    return normalize_unique_id(unique_id)


def get_child_shapes_text(shapes: [Shape]) -> str:
    if not shapes:
        return ""
    return "".join(shape.text for shape in shapes)


def get_x_center(shape: Shape) -> float:
    return float(shape.center_x_y[0])


def get_y_center(shape: Shape) -> float:
    return float(shape.center_x_y[1])


def get_width(shape: Shape) -> float:
    if "Width" in shape.cells:
        return float(shape.cells["Width"].value)

    if "Width" in shape.master_shape.cells:
        return float(shape.master_shape.cells["Width"].value)


def get_height(shape: Shape) -> float:
    if "Height" in shape.cells:
        return float(shape.cells["Height"].value)

    if "Height" in shape.master_shape.cells:
        return float(shape.master_shape.cells["Height"].value)


def get_normalized_angle(shape: Shape) -> float:
    return normalize_angle(get_angle(shape))


def get_angle(shape: Shape) -> float:
    return float(shape.cells["Angle"].value)


def normalize_angle(angle: float) -> float:
    return angle + 2 * pi if angle < 0 else angle


def get_limits(shape: Shape) -> tuple:
    center_x = get_x_center(shape)
    center_y = get_y_center(shape)
    width = get_width(shape)
    height = get_height(shape)

    return (center_x - (width / 2), center_y - (height / 2)), (
        center_x + (width / 2),
        center_y + (height / 2),
    )


def normalize_label(label):
    if not label:
        return label

    # replace by ' ' any '\n'
    label_normalized = label.replace("\n", " ")
    # replace multiple spaces in a row (2 or more) by a single one
    label_normalized = re.sub(r"\s+", " ", label_normalized)
    # strip any leading or trailing space
    label_normalized = label_normalized.strip()

    return label_normalized


def normalize_unique_id(unique_id):
    return re.sub("[{}]", "", unique_id) if unique_id else ""


def deterministic_uuid(source):
    if source:
        random.seed(source)
    return str(uuid.UUID(int=random.getrandbits(128), version=4))


def remove_from_list(collection: [], filter_function, remove_function=None) -> None:
    if collection is None:
        return
    i = 0
    while i < len(collection):
        element = collection[i]
        if filter_function(element):
            remove_function(
                element
            ) if remove_function is not None else collection.remove(element)
        else:
            i += 1


def remove_duplicates(duplicated_list: []):
    unique_list = []

    for element in duplicated_list:
        if element not in unique_list:
            unique_list.append(element)

    return unique_list
