---
title: PipeCAD.Database.DbElementCollection Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.DbElementCollection Class

> Collect elements by fileters for the given element.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

## Properties


## Methods

### `DbElementCollection(element, filter)`

Collect elements by filter for the element.

```py
typeFilter = TypeFilter('SPCO')
world = Project.World

col = DbElementCollection(world, typeFilter)

# Perform collect.
spcoList = col.Perform()
```

### `Perform()`

Perform collect and return the element list.

```py
typeFilter = TypeFilter('SPCO')
world = Project.World

col = DbElementCollection(world, typeFilter)

# Perform collect.
spcoList = col.Perform()
```
