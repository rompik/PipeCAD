---
title: PipeCAD.Database.Project Class
namespace: PipeCAD.Database
kind: Class
---

# PipeCAD.Database.Project Class

> Project in PipeCAD database.

## Requirements

Namespace: PipeCAD.Database

Assembly: python/PipeCAD/Database.pyd

## Properties

### `Current`

Static property: Current project instance.

```py
proj = Project.Current
```

### `Name`

Project name.

```py
proj = Project.Current
proj.Name
```

### `Code`

Project Code.

```py
proj = Project.Current
proj.Code
```

### `Description`

Project description.

```py
proj = Project.Current
proj.Description
```

### `IsOpen`

Check project is opened!

```py
proj = Project.Current
proj.IsOpen
```

### `CanUndo`

Test if an undo action is available.

```py
proj = Project.Current
proj.CanUndo
```

### `CanRedo`

Test if an redo action is available.

```py
proj = Project.Current
proj.CanRedo
```


## Methods

### `GetElement(id)`

Static method to get en Element instance in the project by using id.

```py
elem = Project.GetElement(123)
```

### `GetElement(name)`

Static method get en Element instance in the project by using name.

```py
elem = Project.GetElement('element-name')
```

### `Save()`

Save project modifications to database.

```py
Project.Current.Save()
```

### `Undo()`

Perform undo.

```py
Project.Current.Undo()
```

### `Redo()`

Perform redo.

```py
Project.Current.Redo()
```

### `OpenTransaction()`

Start an undo transaction.

```py
Project.Current.OpenTransaction()
```

### `CommitTransaction()`

Commit an undo transaction.

```py
Project.Current.CommitTransaction()
```

### `AbortTransaction()`

Abort an undo transaction.

```py
Project.Current.AbortTransaction()
```
