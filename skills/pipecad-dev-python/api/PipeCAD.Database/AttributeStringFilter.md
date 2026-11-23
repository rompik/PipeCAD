---
title: PipeCAD.Database.AttributeStringFilter Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.AttributeStringFilter Class

> Represents a filter that checks an element attribute using a supplied string value.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

The example assumes the PipeCAD database API is imported:

```py
from PipeCAD.Database import *
```

## Properties


## Methods

### `AttributeStringFilter(attrName, checkValue)`

Constructs a filter from an attribute name and the value to check.

```py
purpose_filter = AttributeStringFilter('Purpose', 'PIPING')
```
