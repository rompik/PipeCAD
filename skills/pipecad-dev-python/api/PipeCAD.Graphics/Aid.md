---
title: PipeCAD.Graphics.Aid Class
namespace: PipeCAD.Graphics
kind: Class
---

# PipeCAD.Graphics.Aid Class

> Provides static methods for adding, removing, and refreshing temporary graphical aids (such as axes) in the 3D view.

## Requirements

Namespace: PipeCAD.Graphics

Assembly: python/PipeCAD/Graphics.pyd

The examples assume the PipeCAD graphics, geometry, and database APIs are imported and that a project is open:

```py
from PipeCAD.Geometry import *
from PipeCAD.Database import *
from PipeCAD.Graphics import *
```

## Methods

### `NextNumber()`

Returns the next aid number. Pass the number to `AddAxis` and `Remove` to refer to the same aid.

```py
aid_number = Aid.NextNumber()
```

### `AddAxis(position, direction, number)`

Adds an axis aid at `position` pointing along `direction`, identified by `number`. Call `Update` to refresh the view.

```py
# element is a DbElement that has a Pposition/Pdirection point.
point_index = 1
position = element.GetPosition('Pposition', point_index, Project.World)
direction = element.GetDirection('Pdirection', point_index, Project.World)

aid_number = Aid.NextNumber()
Aid.AddAxis(position, direction, aid_number)
Aid.Update()
```

### `Remove(number)`

Removes the aid identified by `number`. Call `Update` to refresh the view.

```py
Aid.Remove(aid_number)
Aid.Update()
```

### `Update()`

Refreshes the 3D view after aids have been added or removed.

```py
Aid.Update()
```
