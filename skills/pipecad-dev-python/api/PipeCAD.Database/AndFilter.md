---
title: PipeCAD.Database.AndFilter Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.AndFilter Class

> Represents a filter that matches elements satisfying every component filter.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

The examples assume the PipeCAD database API is imported:

```py
from PipeCAD.Database import *
```

## Properties


## Methods

### `AndFilter()`

Creates an `AndFilter` without initial component filters. Use `Add(filter)` to
add filters.

```py
combined_filter = AndFilter()
```

### `AndFilter(filter1, filter2)`

Creates a filter that combines two filters.

```py
type_filter = TypeFilter('SPEC')
purpose_filter = AttributeStringFilter('Purpose', 'PIPING')

combined_filter = AndFilter(type_filter, purpose_filter)
```

### `Add(filter)`

Adds the specified filter to this combined filter.

```py
type_filter = TypeFilter('SITE')
purpose_filter = AttributeStringFilter('Purpose', 'PIPING')

combined_filter = AndFilter()
combined_filter.Add(type_filter)
combined_filter.Add(purpose_filter)
```
