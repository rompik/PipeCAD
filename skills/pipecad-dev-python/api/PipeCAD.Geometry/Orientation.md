---
title: PipeCAD.Geometry.Orientation Class
namespace: PipeCAD.Geometry
kind: Class
---

# PipeCAD.Geometry.Orientation Class

> Represents a coordinate system.

## Requirements

Namespace: PipeCAD.Geometry

Assembly: python/PipeCAD/Geometry.pyd

The examples assume the PipeCAD geometry API is imported:

```py
from PipeCAD.Geometry import *
```

## Properties


## Methods

### `Orientation(Direction dx, Direction dy)`

Constructs a coordinate system from two directions.

```py
x_direction = Direction(1, 0, 0)
y_direction = Direction(0, 1, 0)

orientation = Orientation(x_direction, y_direction)
```

### `XDirection()`

Returns the X direction of this coordinate system.

```py
x_direction = Direction(1, 0, 0)
y_direction = Direction(0, 1, 0)

orientation = Orientation(x_direction, y_direction)
returned_x_direction = orientation.XDirection()
```

### `YDirection()`

Returns the Y direction of this coordinate system.

```py
x_direction = Direction(1, 0, 0)
y_direction = Direction(0, 1, 0)

orientation = Orientation(x_direction, y_direction)
returned_y_direction = orientation.YDirection()
```
