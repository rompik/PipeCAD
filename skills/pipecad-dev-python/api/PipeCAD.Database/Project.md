---
title: PipeCAD.Database.Project Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.Project Class

> Represents a PipeCAD project and provides access to project metadata and operations.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

The examples assume PipeCAD is running and a project is open. Run this setup first:

```py
from PipeCAD.Database import *

current_project = Project.Current
```

## Properties

### `Current`

Static property. Returns the current project instance.

```py
current_project = Project.Current
```

### `Name`

Returns the name of the current project.

```py
current_project.Name
```

### `Code`

Returns the code of the current project.

```py
current_project.Code
```

### `Description`

Returns the description of the current project.

```py
current_project.Description
```

### `IsOpen`

Returns whether the current project is open.

```py
current_project.IsOpen
```

### `CanUndo`

Returns whether an undo operation is available for the current project.

```py
current_project.CanUndo
```

### `CanRedo`

Returns whether a redo operation is available for the current project.

```py
current_project.CanRedo
```


## Methods

### `GetElement(id)`

Static method that retrieves the element with the specified ID.

```py
element = Project.GetElement(123)
```

### `GetElement(name)`

Static method that retrieves the element with the specified name.

```py
element = Project.GetElement('element-name')
```

### `Save()`

Saves the project's modifications to the database.

```py
current_project.Save()
```

### `Undo()`

Undoes the most recent undoable operation.

```py
current_project.Undo()
```

### `Redo()`

Redoes the most recently undone operation.

```py
current_project.Redo()
```

### `OpenTransaction()`

Starts a transaction for grouping project changes into one undoable operation.

```py
current_project.OpenTransaction()
```

### `CommitTransaction()`

Commits the current transaction.

```py
current_project.CommitTransaction()
```

### `AbortTransaction()`

Aborts the current transaction.

```py
current_project.AbortTransaction()
```
