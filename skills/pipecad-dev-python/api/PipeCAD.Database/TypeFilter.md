---
title: PipeCAD.Database.TypeFilter Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.TypeFilter Class

> Represents a filter for elements of specified types.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

The example assumes the PipeCAD database API is imported:

```py
from PipeCAD.Database import *
```

## Properties


## Methods

### `TypeFilter(type)`

Constructs a filter for the specified element type.

```py
type_filter = TypeFilter('SPEC')
```

### `Add(type)`

Adds an element type to this filter.

```py
type_filter = TypeFilter('SPEC')
type_filter.Add('SELE')
type_filter.Add('SPCO')
```
