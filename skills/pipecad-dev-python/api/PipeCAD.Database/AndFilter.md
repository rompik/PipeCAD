---
title: PipeCAD.Database.AndFilter Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.AndFilter Class

> Combines filters so that an element must satisfy each filter.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

The examples assume the PipeCAD database API is imported:

```py
from PipeCAD.Database import *
```

## Properties


## Methods

### `AndFilter(filter1, filter2)`

Constructs a filter that combines two filters.

```py
type_filter = TypeFilter('SPEC')
purpose_filter = AttributeStringFilter('Purpose', 'PIPING')

combined_filter = AndFilter(type_filter, purpose_filter)
```

### `Add(filter)`

Adds the specified filter to this combined filter.

The existing example uses `AndFilter()` without arguments; that constructor is not documented here.

```py
type_filter = TypeFilter('SITE')
purpose_filter = AttributeStringFilter('Purpose', 'PIPING')

combined_filter = AndFilter()
combined_filter.Add(type_filter)
combined_filter.Add(purpose_filter)
```
