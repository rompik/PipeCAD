---
name: pipecad-dev-python
description: PipeCAD Python 二次开发专家技能。当用户需要编写、调试、解释或审查PipeCAD Python代码--数据访问、元素创建/删除/遍历、属性读写、几何与位置计算、数据库事件处理时，务必使用本技能。
metadata:
  suite: pipecad-dev-skills
  version: "0.1.0"
---

# PipeCAD Python 开发指南

帮助用户使用 PipeCAD 的 Python 接口进行二次开发：查找 API、编写代码、解释现有代码。

## 使用流程

**确定命名空间**：先判断任务属于哪个领域，对应命名空间如下：

   | 领域 | 命名空间 | 关键类型 |
   |------|----------|----------|
   | 独立应用入口 | `PipeCAD.Standalone` | `Standalone` |
   | 项目/数据库 | `PipeCAD.Database` | `Project`, `DbElement`, `DbAttribute`, `DbElementType`, `BaseFilter`, `TypeFilter`, `DbElementCollection` |
   | 几何（点/线/面/方向） | `PipeCAD.Geometry` | `Position`, `Orientation`, `Direction`, `Line`, `Plane`, `LimitsBox`, `Axis` |
   | 图形接口 | `PipeCAD.Graphics` | `DrawListManager`, `DrawList`, `Colour`, `Aid` |

## 核心概念

务必理解 PipeCAD 中的核心概念：

- **`DbElement`**：数据库元素的句柄，操作所有的数据对象。判断"空"元素必须用 `IsNull` 属性（`element.IsNull`），不能与 null 比较。使用之前最好使用属性先判断是否有效 `IsValid`。

- **`DbAttribute`**：属性标识，为了简化属性的查询，统一使用字符串。如 `Name`, `Type`, `Owner`, `Position`等。

- **`DbElementType`**：元素类型标识，为了简化类型的查询，统一使用字符串。如 `SITE`, `ZONE`, `PIPE`等。

- **属性值**：用 `DbElement.GetAsString/GetBool/GetDouble/GetInteger` 等直接取；写值用 `SetAttribute(DbAttribute, 值)`，重载覆盖 string/int/double/bool/DbElement/DbElement[]/Position/Orientation/Direction 等。

所有属性的名称，类型及描述请查看 `data/MetaData.json` 中的 `Attributes`，所有元素类型、包含的属性及层级关系请查看 `data/MetaData.json`中的 `Types`。

## 任务模式

### 1. GUI开发

用户界面开发主要使用 `PythonQt`，语法与 `PySide` 和 `PyQt` 类似， 即 `Qt` 中界面相关的类和功能都可以使用。需要引入 `PythonQt` 相应的库：

```py
from PythonQt.QtCore import *
from PythonQt.QtGui import *
```

下面代码示例为一个简单的窗口实现：

```py
from PythonQt.QtCore import *
from PythonQt.QtGui import *

class HelloDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Hello PipeCAD"))

        self.verticalLayout = QVBoxLayout(self)

        self.labelHello = QLabel(self.tr("Hello PipeCAD!"))

        self.verticalLayout.addWidget(self.labelHello)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
    # setupUi

# HelloDialog
```

对于用户界面上需要被翻译的字符串，必须实现 `tr()` 函数，需要翻译的字符必须使用英文，并调用 `self.tr()`。将上述代码保存为 `PipeCAD/python/Design/General/Hello.py`，在 `PipeCAD` 中的命令窗口中输入以下命令即可以显示出界面窗口：

```py
from PipeCAD.Design.General import Hello

dlg = Hello.HelloDialog()
dlg.show()

```

### 2. 项目接口

```py
from PipeCAD.Database import *

# 当前打开的项目
project = Project.Current

# 项目名称
name = project.Name

# 项目代号
code = project.Code

# 项目描述
desc = project.Description

# 保存
project.Save()

# World 根结点元素
world = Project.World

```

### 3. 查找元素

提供两种查找元素的方法：根据元素ID和名称字符串。对于查找到的元素，使用之前必须使用属性 `IsValid` 进行检查。通过 `DbElement.Current` 来获取当前元素。

```py
from PipeCAD.Database import *

# 通过元素唯一ID来查找
elem = Project.GetElement(123)

# 通过元素名称来查找
elem = Project.GetElement('name')

# 检查元素是否有效
elem.IsValid

# 获取当前元素
ce = DbElement.Current

```

### 4. 创建元素

通过 `DbElement.Create(index, type)` 来创建成员元素。其中 `index` 参数为创建的新元素在成员元素中的位置。当 `index` 小于等于1时，新元素位于第一个；当 `index` 大于成员元素个数时，新元素位于最后一个。第二个参数为元素类型，使用大写字符串，并且使用元素类型的简称 `ShortName`，元素类型简称请参考： `data/MetaData.json` 。

```py
from PipeCAD.Database import *

# 当前元素
ce = DbElement.Current

# 创建元素
elem = ce.Create(2, 'ZONE')

# 在当前元素的子成员中第一个位置创建新元素
elem = ce.Create(1, 'SITE')

```

### 5. 删除元素

通过 `DbElement.Delete()` 来删除元素。。

```py
from PipeCAD.Database import *

# 当前元素
ce = DbElement.Current

# 删除元素
ce.Delete()

```

### 6. 读写属性

在 `DbElement` 中为元素属性的读写提供两种方式：

+ 使用 `GetAttribute()/SetAttribute()`；
+ 直接使用对象属性名称来查询和设值；

优先使用对象属性的方式来读写属性，其中属性的名称必须是在 `data/MetaData.json` 中 `Attributes` 每个属性的 `QueryText`，大驼峰风格的属性名称。

```py
from PipeCAD.Database import *

# 当前元素
ce = DbElement.Current

# 读属性方式1：通过函数根据属性名称来读取属性
name = ce.GetString('Name')

# 读属性方式2：使用对象的属性的方式直接读取属性
name = ce.Name

# 写属性方式1：通过函数根据属性名称来设置属性
ce.SetAttribute('Name', 'new-name')

# 写属性方式2：通过对象的属性方式来设置属性
ce.Name = 'new-name'

```

### 7. 几何属性

元素 `DbElement` 中包含三个几何属性：位置 Position， 方向 Direction 和 坐标系 Orientation。

```py
from PipeCAD.Geometry import *
from PipeCAD.Database import *

# 当前元素
ce = DbElement.Current

# 创建长方体 BOX
box = ce.Create(0, 'BOX')

# 设置长方体的尺寸
box.Xlength = 10
box.Ylength = 20
box.Zlength = 6

# 设置长方体的位置
box.Position = Position(0, 10, 200)

# 设置长方体的坐标系
dx = Direction(0, 1, 0)
dy = Direction(0, 0, 1)
box.Orientation = Orientation(dx, dy)

```

### 8. 元素集合

通过元素集合 `DbElementCollection` 来过滤满足条件的元素集合。

```py
from PipeCAD.Database import *

typeFilter = TypeFilter('SITE')
elem = Project.World

col = DbElementCollection(elem, typeFilter)

siteList = col.Collect()

```

### 9. 事件处理

### 10. 事务机制

PipeCAD 为数据修改提供事务机制，如果想将增删改的数据修改打包成一次 `Undo` 撤销，可以使用事务机制。在数据改变之前先开启事务 `OpenTransaction`，数据改变完成后，提交事务 `CommitTransaction`。有异常报错时，必须终止事务 `AbortTransaction`。

相关接口使用如下：

```py
from PipeCAD.Database import *

try:
    # 开启事务
    Project.Current.OpenTransaction()

    # 数据增删改
    site = DbElement.Current.Create(0, 'SITE')
    site.Name = name
    site.Description = self.textDescription.text
    site.Function = self.textFunction.text
    site.Purpose = self.textPurpose.text

    # 提交事务
    Project.Current.CommitTransaction()
except Exception as ex:
    QMessageBox.critical(self,  '', ex)

    # 当有异常时，必须终止事务
    Project.Current.AbortTransaction()
# try

# 撤销
Project.Current.Undo()

# 重做
Project.Current.Redo()

# 是否可以撤销
canUndo = Project.Current.CanUndo

# 是否可以重做
canRedo = Project.Current.CanRedo
```

### 11. 图形接口


## 参考文档

完整 API 参考（每个类型的全部成员签名与描述）位于本 skill 的：

- `api/<Namespace>/INDEX.md` — 每个命名空间的类型索引（含一句话描述）
- `api/<Namespace>/<完整类型名>.md` — 单个类型文档，包含每个类的名称，功能描述及可用的属性和函数列表。

给出 API 建议后，若用户需要精确签名，务必打开对应类型文档核对，不要凭记忆写。
