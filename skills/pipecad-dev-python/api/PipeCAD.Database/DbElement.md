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

The examples assume PipeCAD is running with an open project and a current element. Run this setup before each example; attribute examples require an element that supports the attribute:

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

For `SetAttribute` and the getter methods, `attrName` is the attribute's `QueryText` from `Attributes` in `data/MetaData.json`.
Use a getter that matches the attribute's type. `SetAttribute` supports the value types listed below; the value type should match the attribute's type in `data/MetaData.json`.
The existing `Weight` examples are retained, but `Weight` is not listed in `data/MetaData.json`; its availability is unconfirmed.

`Create`, `Delete`, and `SetAttribute` modify project data. To group changes into one undoable operation, use a project transaction as described in the [transaction workflow](../../SKILL.md#10-transactions).

### `Create(index, type)`

Creates a child element at the specified position and returns it. `index` is the insertion position: values less than or equal to `1` place the element first, and values greater than the number of child elements place it last. `type` is the uppercase short name of the element type from `Types` in `data/MetaData.json`.

```py
new_element = current_element.Create(1, 'SITE')
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
current_element.SetAttribute('Weight', 1.36)

# Set the attribute directly.
current_element.Weight = 1.36
```

### `SetAttribute(attrName, string)`

Sets the named attribute to a string value.

```py
current_element.SetAttribute('Name', 'new-name')

# Set the attribute directly.
current_element.Name = 'new-name'
```

### `SetAttribute(attrName, Direction)`

Sets the named attribute to a direction value.

```py
direction = Direction(1, 0, 0)
current_element.SetAttribute('Hdirection', direction)

# Set the attribute directly.
current_element.Hdirection = direction
```

### `SetAttribute(attrName, Position)`

Sets the named attribute to a position value.

```py
position = Position(1, 0, 0)
current_element.SetAttribute('Position', position)

# Set the attribute directly.
current_element.Position = position
```

### `SetAttribute(attrName, Orientation)`

Sets the named attribute to an orientation value.

```py
x_direction = Direction(1, 0, 0)
y_direction = Direction(0, 0, 1)
orientation = Orientation(x_direction, y_direction)

current_element.SetAttribute('Orientation', orientation)

# Set the attribute directly.
current_element.Orientation = orientation
```

### `GetInteger(attrName)`

Returns the named attribute's integer value.

```py
area = current_element.GetInteger('Area')

# Read the attribute directly.
area = current_element.Area
```

### `GetDouble(attrName)`

Returns the named attribute's floating-point value.

```py
weight = current_element.GetDouble('Weight')

# Read the attribute directly.
weight = current_element.Weight
```

### `GetBool(attrName)`

Returns the named attribute's boolean value.

```py
is_locked = current_element.GetBool('Lock')

# Read the attribute directly.
is_locked = current_element.Lock
```

### `GetString(attrName)`

Returns the named attribute's string value.

```py
name = current_element.GetString('Name')

# Read the attribute directly.
name = current_element.Name
```

### `GetElement(attrName)`

Returns the `DbElement` referenced by the named attribute.

```py
referenced_element = current_element.GetElement('Ptref')

# Read the attribute directly.
referenced_element = current_element.Ptref
```

### `GetPosition(attrName)`

Returns the named attribute's position value.

```py
position = current_element.GetPosition('Aposition')

# Read the attribute directly.
position = current_element.Aposition
```

### `GetDirection(attrName)`

Returns the named attribute's direction value.

```py
direction = current_element.GetDirection('Hdirection')

# Read the attribute directly.
direction = current_element.Hdirection
```

### `GetOrientation(attrName)`

Returns the named attribute's orientation value.

```py
orientation = current_element.GetOrientation('Orientation')

# Read the attribute directly.
orientation = current_element.Orientation
```
