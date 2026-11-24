---
title: PipeCAD.Database.DbElementCollection Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.DbElementCollection Class

> Represents a collection that retrieves elements from a given element using a filter.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

The examples assume PipeCAD is running with a project open and the database
API imported:

```py
from PipeCAD.Database import *
```

## Properties


## Methods

### `DbElementCollection()`

Creates a collection without an element or filter.

```py
element_collection = DbElementCollection()
```

### `DbElementCollection(element, filter)`

Creates a collection for the specified source `DbElement` and `BaseFilter`.

```py
type_filter = TypeFilter('SPCO')
world_element = Project.World

element_collection = DbElementCollection(world_element, type_filter)

# Perform collect.
matching_elements = element_collection.Perform()
```

### `Perform()`

Collects and returns the matching elements as a `list[DbElement]`.

```py
type_filter = TypeFilter('SPCO')
world_element = Project.World

element_collection = DbElementCollection(world_element, type_filter)

# Perform collect.
matching_elements = element_collection.Perform()
```
