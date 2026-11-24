
---
title: PipeCAD Equipment Example
description: Use python in PipeCAD to create and modify equipment model example.
---

# PipeCAD Equipment Example

You can use primitve such as Box, Cylinder, Dish, Torus, .etc. to construct equipment model, for piping connection, you can create Nozzle. Primitve and nozzle have P-Point, P-Point has position and direction, so you can connect primitve and nozzle by P-Point to change their position for convenient.

## Box

Box has `Xlength`, `Ylength`, `Zlength` to set dimension, and `Position`, `Orientation` to change box location. Box has 7 P-Point: 

+ 0 point is the box center point, direction is Up;
+ 1 point is the center right point (position X is half Xlength), direction is X;
+ 2 point is the center back point (position Y is half Ylength), direction is Y;
+ 3 point is the center top point (position Z is half Zlength), direction is Z;
+ 4 point is the center left point (position X is half -Xlength), direction is -X;
+ 5 point is the center front point (position Y is half -Ylength), direction is -Y;
+ 6 point is the center bottom point (position Z is half -Zlength), direction is -Z.

```py
zone = DbElement.Current

box = zone.CreateLast('BOX')
box.Xlength = 100
box.Ylength = 200
box.Zlength = 30
box.Position = Position(10, 20, 30)

# Get P-Point 0 position: (10, 20, 30)
pos = box.GetPosition('Pposition', 0, Project.World)

# Get P-Point 1 position: (60, 20, 30)
pos = box.GetPosition('Pposition', 1, Project.World)

# Get P-Point 1 direction: X, ie. (1, 0, 0)
dir = box.GetDirection('Pdirection', 1, Project.World)

```

## Cylinder

Cylinder has `Diameter`, `Height` to set dimension, and `Position`, `Orientation` to change location. Cylinder has 3 P-Point: 

+ 0 point is the cylinder point (position Z is half height), direction is Up;
+ 1 point is the cylinder top point, direction is Up;
+ 2 point is the cylinder bottom point, direction is Down;

```py
zone = DbElement.Current

cylinder = zone.CreateLast('CYLI')
cylinder.Diameter = 56
cylinder.Height = 30
cylinder.Position = Position(0, 0, 0)

# Get P-Point 0 position: (0, 0, 0)
pos = cylinder.GetPosition('Pposition', 0, Project.World)

# Get P-Point 1 direction: U, ie. (0, 0, 1)
dir = cylinder.GetDirection('Pdirection', 1, Project.World)

# Get P-Point 1 position: (0, 0, 15)
pos = cylinder.GetPosition('Pposition', 1, Project.World)

# Get P-Point 2 direction: U, ie. (0, 0, -1)
dir = cylinder.GetDirection('Pdirection', 2, Project.World)

# Get P-Point 2 position: (0, 0, -15)
pos = cylinder.GetPosition('Pposition', 2, Project.World)

```

## Dish

Dish has `Diameter`, `Radius`, `Height` to set dimension, and `Position`, `Orientation` to change location. Dish has 3 P-Point: 

+ 0 point is the dish bottom point, direction is Up;
+ 1 point is the dish top point, direction is Up;
+ 2 point is the dish bottom point, direction is Down;

```py
zone = DbElement.Current

dish = zone.CreateLast('DISH')
dish.Diameter = 56
dish.Radius = 10
dish.Height = 30
dish.Position = Position(0, 0, 0)

# Get P-Point 0 position: (0, 0, 0)
pos = dish.GetPosition('Pposition', 0, Project.World)

# Get P-Point 1 direction: U, ie. (0, 0, 1)
dir = dish.GetDirection('Pdirection', 1, Project.World)

# Get P-Point 1 position: (0, 0, 30)
pos = dish.GetPosition('Pposition', 1, Project.World)

# Get P-Point 2 direction: U, ie. (0, 0, -1)
dir = dish.GetDirection('Pdirection', 2, Project.World)

# Get P-Point 2 position: (0, 0, 0)
pos = dish.GetPosition('Pposition', 2, Project.World)

```

## Connect Primitve

You can use `Connect` function to connect two equipment primitive by P-Point for convenient. For example, you can connect P2 of a dish to p1 of a cylinder.

```py
zone = DbElement.Current

cylinder = zone.CreateLast('CYLI')
cylinder.Diameter = 100
cylinder.Height = 500

dish = zone.CreateLast('DISH')
dish.Diameter = 100
dish.Radius = 20
dish.Height = 30

# Connect dish p-point 2 to cylinder p-point 1.
dish.Connect(cylinder, 2, 1)

```
