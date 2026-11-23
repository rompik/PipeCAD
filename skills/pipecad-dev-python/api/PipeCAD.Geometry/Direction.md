---
title: PipeCAD.Geometry.Direction Class
namespace: PipeCAD.Geometry
kind: Class
---

# PipeCAD.Geometry.Direction Class

> Represents a unit vector in 3D space.

## Requirements

Namespace: PipeCAD.Geometry

Assembly: python/PipeCAD/Geometry.pyd

The examples assume the PipeCAD geometry API is imported:

```py
from PipeCAD.Geometry import *
```

## Properties

### `X`

Returns the X component of this direction.

```py
direction = Direction(1, 0, 0)
x_component = direction.X
```

### `Y`

Returns the Y component of this direction.

```py
direction = Direction(1, 0, 0)
y_component = direction.Y
```

### `Z`

Returns the Z component of this direction.

```py
direction = Direction(1, 0, 0)
z_component = direction.Z
```

## Methods

### `Direction()`

Creates a direction with components `(0, 0, 1)`.

```py
direction = Direction()
```

### `Direction(x, y, z)`

Creates a direction from the specified `x`, `y`, and `z` components.

```py
direction = Direction(1, 2, 3)
```

### `IsParallel(dir)`

Returns `True` if the two directions are parallel.

```py
first_direction = Direction(1, 2, 3)
second_direction = Direction(4, 5, 6)

are_parallel = first_direction.IsParallel(second_direction)
```
