"""PCF serialization independent of the PythonQt user interface."""


GAP_TOLERANCE = 1.0


def _text(value):
    if value is None:
        return ""
    return str(value)


def _valid(element):
    return element is not None and bool(getattr(element, "IsValid", True))


def _members(element):
    members = getattr(element, "Members", ())
    return list(members) if members is not None else []


def _number(value):
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return ("%f" % value).rstrip("0").rstrip(".") or "0"
    return _text(value)


def _point_text(position):
    return "%s %s %s" % (
        _number(position.X),
        _number(position.Y),
        _number(position.Z),
    )


def _distance(first, second):
    distance = getattr(first, "Distance", None)
    if callable(distance):
        return float(distance(second))
    return (
        (float(first.X) - float(second.X)) ** 2
        + (float(first.Y) - float(second.Y)) ** 2
        + (float(first.Z) - float(second.Z)) ** 2
    ) ** 0.5


def _reference(element, name):
    value = getattr(element, name, None)
    return value if _valid(value) else None


def _detail_reference(component):
    spref = _reference(component, "Spref")
    return _reference(spref, "Detref")


def component_metadata(component):
    """Return the PCF SKEY, item code and description for a component."""
    detref = _detail_reference(component)
    if detref is None:
        return "", "", ""

    skey = _text(getattr(detref, "Skey", ""))
    item_code = _text(getattr(detref, "Name", ""))
    description = _text(
        getattr(detref, "Rtext", "")
        or getattr(detref, "Stext", "")
        or getattr(detref, "Description", "")
    )
    return skey, item_code, description


def _reference_name(element):
    return _text(getattr(element, "Name", "")) if _valid(element) else ""


def _pipeline(branches):
    if not branches:
        raise ValueError("At least one branch is required for PCF export")
    pipeline = branches[0].Owner
    if not _valid(pipeline):
        raise ValueError("The branch has no valid owner pipeline")
    return pipeline


def _point_position(component, index, world):
    return component.GetPosition("Pposition", int(index), world)


def _point_direction(component, index, world):
    return component.GetDirection("Pdirection", int(index), world)


def _point_bore(component, index, branch, endpoint):
    candidates = (
        ("Abore", "Lbore") if endpoint == "arrival" else ("Lbore", "Abore")
    )
    for name in candidates:
        value = getattr(component, name, None)
        if value is not None and _text(value):
            return value

    point_bores = getattr(component, "Pbores", None)
    if point_bores is not None:
        try:
            return point_bores[int(index)]
        except (IndexError, KeyError, TypeError, ValueError):
            pass

    value = getattr(component, "Bore", None)
    if value is not None and _text(value):
        return value
    return getattr(branch, "Hbore" if endpoint == "arrival" else "Tbore", "")


def _point_connection(component, branch, endpoint):
    values = (
        ("ArriveConnection", "Aconnect")
        if endpoint == "arrival"
        else ("LeaveConnection", "Lconnect")
    )
    for value_name in values:
        value = getattr(component, value_name, "")
        if value:
            return value
    return ""


def _endpoint_fields(position, bore, connection=""):
    fields = _point_text(position) + " " + _number(bore)
    if connection:
        fields += " " + _text(connection)
    return fields


def _pcf_type(component, skey):
    spref = _reference(component, "Spref")
    catref = _reference(spref, "Catref") if spref is not None else None
    value = _text(
        getattr(component, "FullType", "")
        or getattr(component, "Gtype", "")
        or getattr(catref, "Gtype", "")
        or getattr(component, "Type", "")
    ).upper()
    if value.startswith("REDUC") or value in ("REDC", "REDU"):
        return (
            "REDUCER-CONCENTRIC"
            if skey.upper().startswith("RC")
            else "REDUCER-ECCENTRIC"
        )
    aliases = {
        "ELBO": "ELBOW",
        "ELBW": "ELBOW",
        "BEND": "ELBOW",
        "REDU": "REDUCER-ECCENTRIC",
        "VALV": "VALVE",
        "VT": "VALVE",
        "TEE": "TEE",
        "OLET": "OLET",
        "TUBI": "PIPE",
    }
    return aliases.get(value, value)


def _record_header(stream, record_type, identifier):
    stream.write("\n%s" % record_type)
    stream.write("\n    COMPONENT-IDENTIFIER  %d" % identifier)


def _write_pipe(stream, identifier, start, end, start_bore, end_bore,
                item_code="", description="", spec="", cut_length=None):
    _record_header(stream, "PIPE", identifier)
    stream.write("\n    END-POINT  %s" % _endpoint_fields(start, start_bore))
    stream.write("\n    END-POINT  %s" % _endpoint_fields(end, end_bore))
    if spec:
        stream.write("\n    PIPING-SPEC  %s" % spec)
    if item_code:
        stream.write("\n    ITEM-CODE  %s" % item_code)
    if description:
        stream.write("\n    ITEM-DESCRIPTION  %s" % description)
    if cut_length is not None:
        stream.write("\n    CUT-PIECE-LENGTH %s" % _number(cut_length))


def _spindle_name(direction):
    components = (abs(direction.X), abs(direction.Y), abs(direction.Z))
    axis = components.index(max(components))
    value = (direction.X, direction.Y, direction.Z)[axis]
    return (
        ("EAST", "WEST"),
        ("NORTH", "SOUTH"),
        ("UP", "DOWN"),
    )[axis][0 if value > 0 else 1]


def _write_special_records(stream, component, record_type, world, arrive, leave):
    if record_type in ("TEE", "OLET"):
        branch_index = 6 - int(arrive) - int(leave)
        branch_position = _point_position(component, branch_index, world)
        branch_bore = _point_bore(component, branch_index, component.Owner, "leave")
        stream.write("\n    CENTRE-POINT  %s" % _point_text(component.Position))
        stream.write(
            "\n    BRANCH1-POINT  %s" % _endpoint_fields(branch_position, branch_bore)
        )
    elif record_type == "ELBOW":
        stream.write("\n    CENTRE-POINT  %s" % _point_text(component.Position))
    elif record_type == "VALVE":
        try:
            direction = _point_direction(component, 3, world)
        except (AttributeError, IndexError, RuntimeError, TypeError, ValueError):
            return
        stream.write("\n    SPINDLE-DIRECTION  %s" % _spindle_name(direction))


def _write_component(stream, identifier, branch, component, world):
    arrive = int(component.Arrive)
    leave = int(component.Leave)
    arrive_position = _point_position(component, arrive, world)
    leave_position = _point_position(component, leave, world)
    arrive_bore = _point_bore(component, arrive, branch, "arrival")
    leave_bore = _point_bore(component, leave, branch, "leave")
    skey, item_code, description = component_metadata(component)
    record_type = _pcf_type(component, skey)

    _record_header(stream, record_type, identifier)
    stream.write(
        "\n    END-POINT  %s"
        % _endpoint_fields(
            arrive_position,
            arrive_bore,
            _point_connection(component, branch, "arrival"),
        )
    )
    stream.write(
        "\n    END-POINT  %s"
        % _endpoint_fields(
            leave_position,
            leave_bore,
            _point_connection(component, branch, "leave"),
        )
    )
    _write_special_records(
        stream, component, record_type, world, arrive, leave
    )
    if skey:
        stream.write("\n    SKEY  %s" % skey)
    if item_code:
        stream.write("\n    ITEM-CODE  %s" % item_code)
    if description:
        stream.write("\n    ITEM-DESCRIPTION  %s" % description)
    return arrive_position, leave_position, item_code, description


def write_pcf(branches, stream, world):
    """Write a PCF stream from branch elements."""
    branches = list(branches)
    pipeline = _pipeline(branches)
    stream.write("ISOGEN-FILES ISOGEN.FLS\n")
    stream.write("UNITS-BORE        MM\n")
    stream.write("UNITS-CO-ORDS     MM\n")
    stream.write("UNITS-BOLT-LENGTH MM\n")
    stream.write("UNITS-BOLT-DIA    MM\n")
    stream.write("UNITS-WEIGHT      KGS\n")
    stream.write("PIPELINE-REFERENCE %s\n" % _text(pipeline.Name))

    for label, attribute in (
        ("PIPING-SPEC", "Pspec"),
        ("INSULATION-SPEC", "Ispec"),
        ("TRACING-SPEC", "Tspec"),
    ):
        name = _reference_name(getattr(pipeline, attribute, None))
        if name:
            stream.write("    %s  %s\n" % (label, name))

    item_codes = {}
    identifier = 1
    for branch in branches:
        if getattr(branch, "Type", "") != "BRAN":
            continue
        cursor = branch.Hposition
        for component in _members(branch):
            if component.Type == "TUBI":
                arrive_position = component.Aposition
                leave_position = component.Lposition
                bore = component.Lbore
                skey, item_code, description = component_metadata(component)
                if _distance(cursor, arrive_position) > GAP_TOLERANCE:
                    _write_pipe(
                        stream, identifier, cursor, arrive_position,
                        branch.Hbore, bore,
                    )
                    identifier += 1
                _write_pipe(
                    stream, identifier, arrive_position, leave_position,
                    bore, bore, item_code, description,
                    _reference_name(component.Spref),
                    getattr(component, "Itlength", None),
                )
                if item_code:
                    item_codes[item_code] = description
                cursor = leave_position
                identifier += 1
                continue

            arrive_position = _point_position(
                component, int(component.Arrive), world
            )
            if _distance(cursor, arrive_position) > GAP_TOLERANCE:
                _write_pipe(
                    stream, identifier, cursor, arrive_position,
                    _point_bore(component, component.Arrive, branch, "arrival"),
                    _point_bore(component, component.Arrive, branch, "arrival"),
                )
                identifier += 1
            _, cursor, item_code, description = _write_component(
                stream, identifier, branch, component, world
            )
            if item_code:
                item_codes[item_code] = description
            identifier += 1

        if _distance(cursor, branch.Tposition) > GAP_TOLERANCE:
            _write_pipe(
                stream, identifier, cursor, branch.Tposition,
                branch.Tbore, branch.Tbore,
            )
            identifier += 1

    stream.write("\nMATERIALS\n")
    for item_code, description in item_codes.items():
        stream.write("ITEM-CODE %s\n" % item_code)
        stream.write("    DESCRIPTION  %s\n" % description)


def export_file(branches, filename, world):
    """Write branches to a UTF-8 PCF file."""
    with open(filename, "w", encoding="utf-8", newline="\n") as stream:
        write_pcf(branches, stream, world)
