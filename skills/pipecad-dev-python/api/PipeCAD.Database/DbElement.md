---
title: PipeCAD.Database.DbElement Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.DbElement Class

> Methods to read and write data to the element.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

## Properties

### `Current`

Static property: Project current element.

```py
ce = DbElement.Current
```

### `Owner`

Owner element of this element.

```py
ce = DbElement.Current
ce.Owner
```

### `IsNull`

True if this element is null.

```py
ce = DbElement.Current
ce.IsNull
```

### `IsValid`

True if this element is valid.

```py
ce = DbElement.Current
ce.IsValid
```

### `Members`

Get element memeber list

```py
ce = DbElement.Current
ce.Members
```

## Methods

### `Create(index, type)`

Create a new Element at given position in this Element's child list.

```py
ce = DbElement.Current
elem = ce.Create(1, 'SITE')
```

### `Delete()`

Delete this Element.

```py
ce = DbElement.Current
ce.Delete()
```

### `SetAttribute(attrName, int)`

Set Attribute on Element as an integer.

```py
ce = DbElement.Current
ce.SetAttribute('Area', 1)

# Set attribute directly.
ce.Area = 1
```

### `SetAttribute(attrName, bool)`

Set Attribute on Element as boolean.

```py
ce = DbElement.Current
ce.SetAttribute('Lock', True)

# Set attribute directly.
ce.Lock = True
```

### `SetAttribute(attrName, float)`

Set Attribute on Element as double.

```py
ce = DbElement.Current
ce.SetAttribute('Pressure', 1.36)

# Set attribute directly.
ce.Pressure = 1.36
```

### `SetAttribute(attrName, string)`

Set Attribute on Element as string.

```py
ce = DbElement.Current
ce.SetAttribute('Name', 'new-name')

# Set attribute directly.
ce.Name = 'new-name'
```

### `SetAttribute(attrName, Direction)`

Set Attribute on Element as direction.

```py
ce = DbElement.Current

dir = Direction(1, 0, 0)
ce.SetAttribute('Hdirection', dir)

# Set attribute directly.
ce.Hdirection = dir
```

### `SetAttribute(attrName, Position)`

Set Attribute on Element as Position.

```py
ce = DbElement.Current

pos = Position(1, 0, 0)
ce.SetAttribute('Position', pos)

# Set attribute directly.
ce.Position = pos
```

### `SetAttribute(attrName, Orientation)`

Set Attribute on Element as Orientation.

```py
ce = DbElement.Current

dx = Direction(1, 0, 0)
dy = Direction(0, 0, 1)
ori = Orientation(dx, dy)

ce.SetAttribute('Orientation', ori)

# Set attribute directly.
ce.Orientation = ori
```

### `GetInteger(attrName)`

Get integer Attribute value on Element.

```py
ce = DbElement.Current
area = ce.GetInteger('Area')

# Get attribute directly.
area = ce.Area
```

### `GetDouble(attrName)`

Get floating-point Attribute value on Element.

```py
ce = DbElement.Current
w = ce.GetDouble('Weight')

# Get attribute directly.
w = ce.Weight
```

### `GetBool(attrName)`

Get boolean Attribute value on Element.

```py
ce = DbElement.Current
lock = ce.GetBool('Lock')

# Get attribute directly.
lock = ce.Lock
```

### `GetString(attrName)`

Get text value Attribute on Element.

```py
ce = DbElement.Current
name = ce.GetString('Name')

# Get attribute directly.
name = ce.Name
```

### `GetElement(attrName)`

Get Ref attribute on an Element.

```py
ce = DbElement.Current
ptref = ce.GetElement('Ptref')

# Get attribute directly.
ptref = ce.Ptref
```

### `GetPosition(attrName)`

Get position attribute on an Element.

```py
ce = DbElement.Current
pos = ce.GetPosition('Aposition')

# Get attribute directly.
pos = ce.Aposition
```

### `GetDirection(attrName)`

Get direction attribute on an Element.

```py
ce = DbElement.Current
dir = ce.GetDirection('Hdirection')

# Get attribute directly.
dir = ce.Hdirection
```

### `GetOrientation(attrName)`

Get orientation attribute on an Element.

```py
ce = DbElement.Current
ori = ce.GetOrientation('Orientation')

# Get attribute directly.
ori = ce.Orientation
```
