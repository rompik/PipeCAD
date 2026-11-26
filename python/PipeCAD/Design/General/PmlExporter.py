"""Export PipeCAD catalogue and equipment elements as PDMS PML."""

import time


def _text(value):
    if value is None:
        return ""
    return str(value)


def _values(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _members(element):
    return _values(element.Members)


def _valid_reference(element):
    return element is not None and bool(getattr(element, "IsValid", True))


def _pml_name(element):
    name = _text(element.Name)
    return "/" + name if name else ""


def _write_new(stream, pml_type, element):
    stream.write("\nNEW %s%s" % (pml_type, _pml_name(element)))


def _write_expression(stream, key, value):
    value = _text(value)
    if not value:
        return
    if value.startswith("DD"):
        parts = value.split("*", 1)
        if len(parts) == 2:
            stream.write("\n%s %s TIMES %s" % (key, parts[1], parts[0]))
        else:
            stream.write("\n%s %s" % (key, value))
    else:
        stream.write("\n%s (%s)" % (key, value))


def _write_point_expression(stream, key, value):
    value = _text(value).replace("math.tan", "TAN").replace("math.pi", "180")
    if not value:
        return
    if value.startswith("DD"):
        stream.write("\n%s %s" % (key, value))
    else:
        stream.write("\n%s (%s)" % (key, value))


def _write_optional(stream, command, value):
    value = _text(value)
    if value:
        stream.write("\n%s %s" % (command, value))


def _export_sdte(element, stream):
    if element.Type != "SDTE":
        return
    _write_new(stream, "SDTEXT", element)
    stream.write("\nSKEY '%s'" % _text(element.Skey))
    stream.write("\nRTEX (|%s|)" % _text(element.Rtext))
    stream.write("\nSTEX |%s|" % _text(element.Stext))


def _export_text(element, stream):
    if element.Type != "TEXT":
        return
    _write_new(stream, "TEXT", element)
    stream.write("\nSTEX |%s|" % _text(element.Stext))


def _export_scom(element, stream):
    if element.Type != "SCOM":
        return
    _write_new(stream, "SCOMPONENT", element)
    stream.write("\n!!ce.Ptref = !aPtref")
    stream.write("\n!!ce.Gmref = !aGmref")
    stream.write("\nGTYP %s" % _text(element.Gtype))
    parameters = " ".join(_text(value) for value in _values(element.Param))
    if parameters:
        stream.write("\nPARA %s" % parameters)


def _export_ptcar(element, stream):
    if element.Type != "PTCA":
        return
    _write_new(stream, "PTCAR", element)
    stream.write("\nNUMB %d" % int(element.Number))
    _write_optional(stream, "PCON", element.Connection)
    _write_optional(stream, "PBOR", element.Bore)
    _write_optional(stream, "Ptcdirection", element.Direction)
    _write_point_expression(stream, "PX", element.Px)
    _write_point_expression(stream, "PY", element.Py)
    _write_point_expression(stream, "PZ", element.Pz)


def _export_ptaxis(element, stream):
    if element.Type != "PTAX":
        return
    _write_new(stream, "PTAXIS", element)
    stream.write("\nNUMB %d" % int(element.Number))
    _write_optional(stream, "PCON", element.Connection)
    _write_optional(stream, "PBOR", element.Bore)
    _write_point_expression(stream, "PDIS", element.Distance)
    _write_optional(stream, "PAXI", element.Axis)


def _export_ptse(element, stream):
    if element.Type != "PTSE":
        return
    _write_new(stream, "PTSET", element)
    stream.write("\n!aCategory.Ptref = ce")
    stream.write("\n!aPtref = ce")
    for child in _members(element):
        _export_ptcar(child, stream)
        _export_ptaxis(child, stream)


def _export_sbox(element, stream):
    if element.Type != "SBOX":
        return
    _write_new(stream, "SBOX", element)
    stream.write("\nTuflag True")
    for key, attribute in (
        ("Px", "Px"),
        ("Py", "Py"),
        ("Pz", "Pz"),
        ("Pxlength", "Pxlength"),
        ("Pylength", "Pylength"),
        ("Pzlength", "Pzlength"),
    ):
        _write_expression(stream, key, getattr(element, attribute))


def _export_scyl(element, stream):
    if element.Type != "SCYL":
        return
    _write_new(stream, "SCYLINDER", element)
    stream.write("\nTuflag True")
    _write_expression(stream, "Pdistance", element.Pdistance)
    _write_expression(stream, "Pdiameter", element.Pdiameter)
    _write_expression(stream, "Pheight", element.Pheight)
    _write_optional(stream, "Paxis", element.Paxis)


def _export_lsno(element, stream):
    if element.Type != "LSNO":
        return
    _write_new(stream, "LSNOUT", element)
    stream.write("\nTuflag True")
    for key, attribute in (
        ("Ptdistance", "Ptdistance"),
        ("Pbdistance", "Pbdistance"),
        ("Ptdiameter", "Ptdiameter"),
        ("Pbdiameter", "Pbdiameter"),
        ("Poffset", "Poffset"),
    ):
        _write_expression(stream, key, getattr(element, attribute))
    _write_optional(stream, "Paaxis", element.Paaxis)
    _write_optional(stream, "Pbaxis", element.Pbaxis)


def _export_sdsh(element, stream):
    if element.Type != "SDSH":
        return
    _write_new(stream, "SDSH", element)
    stream.write("\nTuflag True")
    _write_optional(stream, "Paxis", element.Paxis)
    for key, attribute in (
        ("Pdistance", "Pdistance"),
        ("Pheight", "Pheight"),
        ("Pradius", "Pradius"),
        ("Pdiameter", "Pdiameter"),
    ):
        _write_expression(stream, key, getattr(element, attribute))


def _export_scto(element, stream):
    if element.Type != "SCTO":
        return
    _write_new(stream, "SCTORUS", element)
    stream.write("\nTuflag True")
    _write_optional(stream, "Paaxis", element.Paaxis)
    _write_optional(stream, "Pbaxis", element.Pbaxis)
    _write_expression(stream, "Pdiameter", element.Pdiameter)


def _export_gmse(element, stream):
    if element.Type != "GMSE":
        return
    _write_new(stream, "GMSET", element)
    stream.write("\n!aCategory.Gmref = ce")
    stream.write("\n!aGmref = ce")
    exporters = (
        _export_sbox,
        _export_scyl,
        _export_lsno,
        _export_sdsh,
        _export_scto,
    )
    for child in _members(element):
        for exporter in exporters:
            exporter(child, stream)


def _export_category(element, stream):
    if element.Type != "CATE":
        return
    _write_new(stream, "CATEGORY", element)
    _write_optional(stream, "PURP", element.Purpose)
    stream.write("\nDESC |%s|" % _text(element.Description))
    stream.write("\nGTYP %s" % _text(element.Gtype))
    stream.write("\n!aCategory = ce")
    stream.write("\n!aPtref = nulref")
    stream.write("\n!aGmref = nulref")
    exporters = (
        _export_sdte,
        _export_text,
        _export_ptse,
        _export_gmse,
        _export_scom,
    )
    for child in _members(element):
        for exporter in exporters:
            exporter(child, stream)


def _export_section(element, stream):
    if element.Type != "SECT":
        return
    _write_new(stream, "SECTION", element)
    _write_optional(stream, "PURP", element.Purpose)
    for child in _members(element):
        _export_category(child, stream)


def export_catalogue(element, stream):
    """Write a CATA hierarchy to an open text stream."""
    if element.Type != "CATA":
        return False
    _write_new(stream, "CATALOGUE", element)
    _write_optional(stream, "PURP", element.Purpose)
    for child in _members(element):
        _export_section(child, stream)
    return True


def _write_position(stream, position):
    stream.write(
        "\nPOS E%f N%f U%f" % (position.X, position.Y, position.Z)
    )


def _write_orientation(stream, orientation):
    x_direction = orientation.XDirection()
    y_direction = orientation.YDirection()
    stream.write("\n!aDx = object Direction('E')")
    stream.write("\n!aDy = object Direction('N')")
    stream.write("\n!aDx.east = %f" % x_direction.X)
    stream.write("\n!aDx.north = %f" % x_direction.Y)
    stream.write("\n!aDx.up = %f" % x_direction.Z)
    stream.write("\n!aDy.east = %f" % y_direction.X)
    stream.write("\n!aDy.north = %f" % y_direction.Y)
    stream.write("\n!aDy.up = %f" % y_direction.Z)
    stream.write("\nORI X is $!aDx and Y is $!aDy")


def _export_extrusion(element, stream):
    stream.write("\nNEW EXTR HEIG %f" % element.Height)
    stream.write("\n!aExtrItem = ce")
    for child in _members(element):
        if child.Type == "LOOP":
            stream.write("\nNEW LOOP")
            for vertex in _members(child):
                if vertex.Type == "VERT":
                    stream.write("\nNEW VERT")
                    _write_position(stream, vertex.Position)
        elif child.Type == "NXTR":
            stream.write("\nNEW NXTR HEIG %f" % child.Height)
            for loop in _members(child):
                if loop.Type != "LOOP":
                    continue
                stream.write("\nNEW LOOP")
                for vertex in _members(loop):
                    if vertex.Type == "VERT":
                        stream.write("\nNEW VERT")
                        _write_position(stream, vertex.Position)
    stream.write("\n!!ce = !aExtrItem")


def _export_primitive(element, stream):
    if element.Type == "CYLI":
        stream.write(
            "\nNEW CYLINDER DIAM %f HEIG %f"
            % (element.Diameter, element.Height)
        )
    elif element.Type == "BOX":
        stream.write(
            "\nNEW BOX XLEN %f YLEN %f ZLEN %f"
            % (element.Xlength, element.Ylength, element.Zlength)
        )
    elif element.Type == "DISH":
        stream.write(
            "\nNEW DISH DIAM %f HEIG %f RADI %f"
            % (element.Diameter, element.Height, element.Radius)
        )
    elif element.Type == "CONE":
        stream.write(
            "\nNEW CONE DTOP %f DBOT %f HEIG %f"
            % (element.Dtop, element.Dbottom, element.Height)
        )
    elif element.Type == "EXTR":
        _export_extrusion(element, stream)
    elif element.Type == "NOZZ":
        _write_new(stream, "NOZZ", element)
        stream.write(" HEIG %f" % element.Height)
        if _valid_reference(element.Catref):
            stream.write("\nCATR SCOMPONENT /" + _text(element.Catref.Name))
            stream.write("\nhandle ANY")
            stream.write("\n$p Bad Catref of Nozzle " + _text(element.Name))
            stream.write("\nendhandle")
    else:
        return False
    _write_position(stream, element.Position)
    _write_orientation(stream, element.Orientation)
    stream.write("\n")
    return True


def export_equipment(element, stream):
    """Write an EQUI hierarchy to an open text stream."""
    if element.Type != "EQUI":
        return False
    _write_new(stream, "EQUIPMENT", element)
    _write_position(stream, element.Position)
    stream.write("\n")
    for child in _members(element):
        _export_primitive(child, stream)
    return True


def export_element(element, stream):
    """Write one supported element hierarchy to an open text stream."""
    if export_equipment(element, stream):
        return True
    return export_catalogue(element, stream)


def write_macro(element, stream, timestamp=None):
    """Write a complete PML macro for *element* to *stream*."""
    if timestamp is None:
        timestamp = time.asctime(time.localtime(time.time()))
    stream.write("$S-  -- Synonym translation OFF")
    stream.write("\n-- ----------------------------------------------------------------")
    stream.write("\n-- Data Listing    Date : " + timestamp)
    stream.write("\n-- Exported by PipeCAD.\n")
    stream.write("\nONERROR GOLABEL /ERROR3\n")
    stream.write("\nINPUT BEGIN")
    if not export_element(element, stream):
        raise ValueError(
            "Unsupported PML export element type: %s" % _text(element.Type)
        )
    stream.write("\nINPUT END %s" % _text(element.Type))
    stream.write("\nINPUT FINISH\n")
    stream.write("\n-- Switch synonyms back on if an error occurs.")
    stream.write("\nLABEL /ERROR3")
    stream.write("\nhandle ANY")
    stream.write("\n$S+")
    stream.write("\nRETURN ERROR")
    stream.write("\nendhandle\n")
    stream.write("\n-- End Data Listing    Date : " + timestamp)
    stream.write("\n$S+  -- Synonym translation ON")
    stream.write("\n-- ----------------------------------------------------------------")
    stream.write("\n")


def export_file(element, filename, timestamp=None):
    """Export an element hierarchy to a UTF-8 PML file."""
    with open(filename, "w", encoding="utf-8", newline="\n") as stream:
        write_macro(element, stream, timestamp)


def _save_filename(dialog, parent):
    selected = dialog.getSaveFileName(
        parent,
        parent.tr("Export PDMS PML"),
        "",
        parent.tr("PDMS PML Macro (*.pml)"),
    )
    if isinstance(selected, (tuple, list)):
        return selected[0]
    return selected


def Export():
    """Export the current PipeCAD element using a save-file dialog."""
    from PythonQt.QtGui import QFileDialog, QMessageBox
    from PipeCAD.Database import DbElement
    from PipeCAD.GUI import MainWindow

    element = DbElement.Current
    if element is None or not element.IsValid:
        QMessageBox.critical(
            MainWindow, "", MainWindow.tr("Please select item to export!")
        )
        return

    filename = _save_filename(QFileDialog, MainWindow)
    if not filename:
        return

    try:
        export_file(element, filename)
    except (AttributeError, OSError, TypeError, ValueError) as error:
        QMessageBox.critical(MainWindow, MainWindow.tr("PML Export"), str(error))
        return

    QMessageBox.information(
        MainWindow, MainWindow.tr("PML Export"), MainWindow.tr(
            "Export PDMS PML finished."
        )
    )
