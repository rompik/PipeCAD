---
name: pipecad-dev-python
description: Expert skill for PipeCAD Python development. Use this skill whenever the user needs to write, debug, explain, or review PipeCAD Python code for data access, element creation/deletion/iteration, attribute reading and writing, geometry and position calculations, or database event handling.
metadata:
  suite: pipecad-dev-skills
  version: "0.1.0"
---

# PipeCAD Python Development Guide

Help users with PipeCAD Python API development: find APIs, write code, and explain existing code.

## Workflow

**Determine the namespace**: First identify the relevant area and its namespace:

   | Area | Namespace | Key types |
   |------|----------|----------|
   | Standalone application entry point | `PipeCAD.Standalone` | `Standalone` |
   | Project/database | `PipeCAD.Database` | `Project`, `DbElement`, `DbAttribute`, `DbElementType`, `BaseFilter`, `TypeFilter`, `DbElementCollection` |
   | Geometry (points/lines/planes/directions) | `PipeCAD.Geometry` | `Position`, `Orientation`, `Direction`, `Line`, `Plane`, `LimitsBox`, `Axis` |
   | Graphics interface | `PipeCAD.Graphics` | `DrawListManager`, `DrawList`, `Colour`, `Aid` |

## Core concepts

Be sure to understand these core PipeCAD concepts:

- **`DbElement`**: A handle to a database element used to operate on all data objects. Check whether an element is "null" using the `IsNull` property (`element.IsNull`); do not compare it with null. Before using an element, it is best to check that it is valid with the `IsValid` property.

- **`DbAttribute`**: An attribute identifier. Attribute queries use strings for simplicity, such as `Name`, `Type`, `Owner`, and `Position`.

- **`DbElementType`**: An element type identifier. Element type queries use strings for simplicity, such as `SITE`, `ZONE`, and `PIPE`.

- **Attribute values**: Read values directly with methods such as `DbElement.GetAsString/GetBool/GetDouble/GetInteger`. Write values with `SetAttribute(DbAttribute, value)`, which is overloaded for string/int/double/bool/DbElement/DbElement[]/Position/Orientation/Direction and other types.

For the names, types, and descriptions of all attributes, see `Attributes` in `data/MetaData.json`. For all element types, their attributes, and their hierarchy, see `Types` in `data/MetaData.json`.

## Task patterns

### 1. GUI development

User interfaces are primarily developed with `PythonQt`, whose syntax is similar to `PySide` and `PyQt`. This means Qt's UI-related classes and features can be used. Import the corresponding `PythonQt` libraries:

```py
from PythonQt.QtCore import *
from PythonQt.QtGui import *
```

The following code demonstrates a simple window:

```py
from PythonQt.QtCore import *
from PythonQt.QtGui import *

class HelloDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Hello PipeCAD"))

        self.verticalLayout = QVBoxLayout(self)

        self.labelHello = QLabel(self.tr("Hello PipeCAD!"))

        self.verticalLayout.addWidget(self.labelHello)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
    # setupUi

# HelloDialog
```

For strings in the user interface that need to be translated, implement the `tr()` function. The translatable strings must be in English and passed to `self.tr()`. Save the code above as `PipeCAD/python/Design/General/Hello.py`, then enter the following commands in the PipeCAD command window to display the UI:

```py
from PipeCAD.Design.General import Hello

dlg = Hello.HelloDialog()
dlg.show()

```

PipeCAD uses the `PIPECAD_LANG` environment variable to select the interface language. For `PIPECAD_LANG=zh_CN`, it looks for `zh_CN.qm` in the `i18n` directory. Two batch files support translation: `lupdate.bat` updates translations from Python files, and `lrelease.bat` compiles translated `ts` files into `qm` files in `i18n`.

### 2. Project API

```py
from PipeCAD.Database import *

# Currently open project
project = Project.Current

# Project name
name = project.Name

# Project code
code = project.Code

# Project description
desc = project.Description

# Save
project.Save()

# World root element
world = Project.World

```

### 3. Find elements

There are two ways to find elements: by element ID or by name string. Before using a found element, check it with the `IsValid` property. Use `DbElement.Current` to get the current element.

```py
from PipeCAD.Database import *

# Find by unique element ID
elem = Project.GetElement(123)

# Find by element name
elem = Project.GetElement('name')

# Check whether the element is valid
elem.IsValid

# Get the current element
ce = DbElement.Current

```

### 4. Create elements

Create a child element with `DbElement.Create(index, type)`. The `index` parameter specifies the new element's position among the child elements. If `index` is less than or equal to 1, the new element is placed first; if `index` is greater than the number of child elements, it is placed last. The second parameter is the element type, specified as an uppercase string using the element type's short name, `ShortName`. See `data/MetaData.json` for element type short names.

```py
from PipeCAD.Database import *

# Current element
ce = DbElement.Current

# Create an element
elem = ce.Create(2, 'ZONE')

# Create a new element as the first child of the current element
elem = ce.Create(1, 'SITE')

```

### 5. Delete elements

Delete an element with `DbElement.Delete()`.

```py
from PipeCAD.Database import *

# Current element
ce = DbElement.Current

# Delete the element
ce.Delete()

```

### 6. Read and write attributes

`DbElement` provides two ways to read and write element attributes:

+ Use `GetAttribute()/SetAttribute()`.
+ Access or set values directly using object property names.

Prefer accessing attributes through object properties. The property name must be the attribute's `QueryText` from `Attributes` in `data/MetaData.json`, using PascalCase.

```py
from PipeCAD.Database import *

# Current element
ce = DbElement.Current

# Read attribute, method 1: use a function with the attribute name
name = ce.GetString('Name')

# Read attribute, method 2: access it directly as an object property
name = ce.Name

# Write attribute, method 1: use a function with the attribute name
ce.SetAttribute('Name', 'new-name')

# Write attribute, method 2: set it directly as an object property
ce.Name = 'new-name'

```

### 7. Geometry properties

The `DbElement` element has three geometry properties: position (`Position`), direction (`Direction`), and coordinate system (`Orientation`).

```py
from PipeCAD.Geometry import *
from PipeCAD.Database import *

# Current element
ce = DbElement.Current

# Create a BOX cuboid
box = ce.Create(0, 'BOX')

# Set the cuboid dimensions
box.Xlength = 10
box.Ylength = 20
box.Zlength = 6

# Set the cuboid position
box.Position = Position(0, 10, 200)

# Set the cuboid coordinate system
dx = Direction(0, 1, 0)
dy = Direction(0, 0, 1)
box.Orientation = Orientation(dx, dy)

```

### 8. Element collections

Use the `DbElementCollection` element collection to filter elements that meet the specified criteria.

```py
from PipeCAD.Database import *

typeFilter = TypeFilter('SITE')
elem = Project.World

col = DbElementCollection(elem, typeFilter)

siteList = col.Perform()

```

### 9. Event handling

### 10. Transactions

PipeCAD provides transactions for data modifications. To group data additions, deletions, and changes into a single `Undo` operation, use a transaction. Start it with `OpenTransaction` before changing data, then commit it with `CommitTransaction` when finished. If an exception occurs, you must abort the transaction with `AbortTransaction`.

Use the API as follows:

```py
from PipeCAD.Database import *

try:
    # Start a transaction
    Project.Current.OpenTransaction()

    # Add, delete, or modify data
    site = DbElement.Current.Create(0, 'SITE')
    site.Name = name
    site.Description = self.textDescription.text
    site.Function = self.textFunction.text
    site.Purpose = self.textPurpose.text

    # Commit the transaction
    Project.Current.CommitTransaction()
except Exception as ex:
    QMessageBox.critical(self,  '', ex)

    # Abort the transaction if an exception occurs
    Project.Current.AbortTransaction()
# try

# Undo
Project.Current.Undo()

# Redo
Project.Current.Redo()

# Whether undo is available
canUndo = Project.Current.CanUndo

# Whether redo is available
canRedo = Project.Current.CanRedo
```

### 11. Graphics API


## Reference documentation

The complete API reference (signatures and descriptions for all members of each type) is located in this skill:

- `api/<Namespace>/INDEX.md` — Type index for each namespace, including a one-sentence description.
- `api/<Namespace>/<FullTypeName>.md` — Single-type documentation containing the class name, a description of its functionality, and a list of available properties and functions.

After recommending an API, if the user needs an exact signature, be sure to check the corresponding type documentation rather than relying on memory.
