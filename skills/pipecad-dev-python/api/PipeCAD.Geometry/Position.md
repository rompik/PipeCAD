---
title: PipeCAD.Geometry.Position Class
namespace: PipeCAD.Geometry
kind: Class
---

# PipeCAD.Geometry.Position Class

> Represents a position in 3D space.

## Requirements

Namespace: PipeCAD.Geometry

Assembly: python/PipeCAD/Geometry.pyd

The examples assume the PipeCAD geometry API is imported:

```py
from PipeCAD.Geometry import *
```

## Properties

### `X`

Returns the X coordinate of this position.

```py
position = Position(1, 2, 3)
x_coordinate = position.X
```

### `Y`

Returns the Y coordinate of this position.

```py
position = Position(1, 2, 3)
y_coordinate = position.Y
```

### `Z`

Returns the Z coordinate of this position.

```py
position = Position(1, 2, 3)
z_coordinate = position.Z
```

## Methods

### `Position()`

Creates a position with coordinates `(0, 0, 0)`.

```py
position = Position()
```

### `Position(x, y, z)`

Creates a position from the specified `x`, `y`, and `z` coordinates.

```py
position = Position(1, 2, 3)
```

### `Distance(pos)`

Returns the distance between this position and the specified position.

```py
first_position = Position(1, 2, 3)
second_position = Position(4, 5, 6)

distance = first_position.Distance(second_position)
```
