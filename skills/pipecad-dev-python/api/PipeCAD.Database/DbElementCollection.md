---
title: PipeCAD.Database.DbElementCollection Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.DbElementCollection Class

> Collects elements from a given element using a filter.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

The examples assume the PipeCAD database API is imported:

```py
from PipeCAD.Database import *
```

## Properties


## Methods

### `DbElementCollection(element, filter)`

Creates a collection for the specified element and filter.

```py
type_filter = TypeFilter('SPCO')
world_element = Project.World

element_collection = DbElementCollection(world_element, type_filter)

# Perform collect.
matching_elements = element_collection.Perform()
```

### `Perform()`

Collects and returns the elements that match the filter.

```py
type_filter = TypeFilter('SPCO')
world_element = Project.World

element_collection = DbElementCollection(world_element, type_filter)

# Perform collect.
matching_elements = element_collection.Perform()
```
