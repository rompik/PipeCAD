---
title: PipeCAD.Database.TypeFilter Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.TypeFilter Class

> Type fitler for DbElementCollection.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

## Properties


## Methods

### `TypeFilter(type)`

Construct a type filter with the given element type string.

```py
typeFilter = TypeFilter('SPEC')
```

### `Add(type)`

Add element type for the filter.

```py
typeFilter = TypeFilter('SPEC')
typeFilter.Add('SELE')
typeFitler.Add('SPCO')
```
