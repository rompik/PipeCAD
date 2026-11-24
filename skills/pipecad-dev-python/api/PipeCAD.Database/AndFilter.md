---
title: PipeCAD.Database.AndFilter Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.AndFilter Class

> And fitler for DbElementCollection. You can set several filters to collect elemenet, the elemenet must valid for all the filters.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

## Properties


## Methods

### `AndFilter()`

Construct a and filter without filters. Then you can add filters by `Add(filter)` method.

```py
filter1 = TypeFilter('SITE')
filter2 = AttributeStringFilter('Purpose', 'PIPING')

andFilter = AndFilter()
andFilter.Add(filter1)
andFilter.Add(filter2)
```

### `AndFilter(filter1, filter2)`

Construct a and filter with two filters.

```py
filter1 = TypeFilter('SPEC')
filter2 = AttributeStringFilter('Purpose', 'PIPING')

andFilter = AndFilter(filter1, filter2)
```

### `Add(filter)`

Add filter to the and filter.

```py
filter1 = TypeFilter('SITE')
filter2 = AttributeStringFilter('Purpose', 'PIPING')

andFilter = AndFilter()
andFilter.Add(filter1)
andFilter.Add(filter2)
```
