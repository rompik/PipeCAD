---
title: PipeCAD.Database.DbElement Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.DbElement Class

> Represents a database element and provides properties and methods to inspect and modify it.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

The examples assume PipeCAD is running with an open project and a current
element. Run this setup before each example; use an element that supports the
attributes or P-points referenced by that example:

```py
from PipeCAD.Database import *
from PipeCAD.Geometry import *

current_element = DbElement.Current
```

## Properties

### `Current`

Static property. Returns the current element in the project.

```py
current_element = DbElement.Current
```

### `Owner`

Returns the element that owns this element.

```py
current_element.Owner
```

### `IsNull`

Returns whether this element is null.

```py
current_element.IsNull
```

### `IsValid`

Returns whether this element is valid.

```py
current_element.IsValid
```

### `Members`

Returns this element's child elements.

```py
current_element.Members
```

## Methods

`Connect`, `Create`, `CreateLast`, `Delete`, and `SetAttribute` modify project
data. To group changes into one undoable operation, use a project transaction
as described in the [transaction workflow](../../SKILL.md#10-transactions).

`SetAttribute` accepts a `DbAttribute` or string attribute name and supports
boolean, integer, floating-point, string, and `DbElement` values. It returns
`None`.

### `Create(index, type)`

Creates a child element at the specified position and returns a `DbElement`.
`type` is the element type's short name from `Types` in
`data/MetaData.json`.

```py
new_element = current_element.Create(1, 'SITE')
```

### `CreateLast(type)`

Creates a child element at the end of this element's child list and returns it.
`type` is the uppercase short name of the element type from `Types` in
`data/MetaData.json`.

```py
new_element = current_element.CreateLast('CYLI')
```

### `Delete()`

Deletes this element.

```py
current_element.Delete()
```

### `SetAttribute(attrName, int)`

Sets the named attribute to an integer value.

```py
current_element.SetAttribute('Area', 1)

# Set the attribute directly.
current_element.Area = 1
```

### `SetAttribute(attrName, bool)`

Sets the named attribute to a boolean value.

```py
current_element.SetAttribute('Lock', True)

# Set the attribute directly.
current_element.Lock = True
```

### `SetAttribute(attrName, float)`

Sets the named attribute to a floating-point value.

```py
current_element.SetAttribute('Pressure', 1.36)

# Set the attribute directly.
current_element.Pressure = 1.36
```

### `SetAttribute(attrName, string)`

Sets the named attribute to a string value.

```py
current_element.SetAttribute('Name', 'new-name')

# Set the attribute directly.
current_element.Name = 'new-name'
```

### `GetInteger(attrName)`

Accepts a `DbAttribute` or string attribute name and returns an integer.

```py
area = current_element.GetInteger('Area')

# Read the attribute directly.
area = current_element.Area
```

### `GetDouble(DbAttribute)`

Returns the floating-point value for the specified `DbAttribute`.

```py
pressure_attribute = DbAttribute.GetAttribute('Pressure')
pressure = current_element.GetDouble(pressure_attribute)

# Read the attribute directly.
pressure = current_element.Pressure
```

### `GetBool(attrName)`

Accepts a `DbAttribute` or string attribute name and returns a boolean.

```py
is_locked = current_element.GetBool('Lock')

# Read the attribute directly.
is_locked = current_element.Lock
```

### `GetString(attrName)`

Accepts a `DbAttribute` or string attribute name and returns a string.

```py
name = current_element.GetString('Name')

# Read the attribute directly.
name = current_element.Name
```

### `GetElement(DbAttribute)`

Returns the `DbElement` referenced by the specified `DbAttribute`.

```py
element_attribute = DbAttribute.GetAttribute('Ptref')
referenced_element = current_element.GetElement(element_attribute)

# Read the attribute directly.
referenced_element = current_element.Ptref
```

### `GetPosition(attrName, index, reference)`

Overloads accept a `DbAttribute`; a string attribute name and integer index;
or a string attribute name, integer index, and reference `DbElement`. Each
returns a `Position`.

```py
point_index = 0
world_element = Project.World
position = current_element.GetPosition(
    'Pposition', point_index, world_element
)
```

### `GetDirection(attrName, index, reference)`

Accepts an attribute name, index, and reference `DbElement`; returns a
`Direction`.

```py
point_index = 1
world_element = Project.World
direction = current_element.GetDirection(
    'Pdirection', point_index, world_element
)
```

### `Connect(toElement, p1, p2)`

Connects P-point `p1` of this element to P-point `p2` of `toElement`
(`DbElement`). The point identifiers accept integers. Returns `None`.

```py
cylinder = current_element.CreateLast('CYLI')
cylinder.Diameter = 100
cylinder.Height = 500

dish = current_element.CreateLast('DISH')
dish.Diameter = 100
dish.Radius = 20
dish.Height = 30

# Connect dish P-point 2 to cylinder P-point 1.
dish.Connect(cylinder, 2, 1)
```

## Geometry properties

The examples below assign geometry values through element properties:

```py
position = Position(1, 0, 0)
current_element.Position = position

x_direction = Direction(1, 0, 0)
y_direction = Direction(0, 0, 1)
orientation = Orientation(x_direction, y_direction)
current_element.Orientation = orientation
```
