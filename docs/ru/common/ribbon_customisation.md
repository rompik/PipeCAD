# Настройка ленточного меню
Приложение PipeCAD имеет ленточное меню, которое может быть настроено с помощью формы Customize Dialog.
Чтобы добавить новое меню необходимо выполнить следующие два действия:

To do it there will need to update uic file (for example: PipeCAD.Design.uic ) by adding new line:
```xml
	<Action Key="run_sample" Text="Run Sample" Icon=":/PipeCad/Resources/project_import.png" ToolTip="Run Sample" Module="omp.sample" Function="omp.sample.ShowSample()" />
```
After that in module where you need to add button for calling utility open Ribbon menu editor by pressing button Customisation ![Ribbon Menu Editor](../../images/icons/customisation.png) located in right top conner of ribbon:

![Настройка ленточного меню](../../images/common/ribbon_customisation/menu_customisation_en.png)

In opened form it possible to create dedicated Tab for developed utilities by pressing button **New Category** in the right part of form.

![Customisation Dialog](../../images/common/ribbon_customisation/customize_dialog_en.png)

After creating new element, there is need to select it and press button **Rename** to name it correctly. In our case we will create Tab and call it **OMP**:

![Create new Tab](../../images/common/ribbon_customisation/new_tab_en.png)

Inside this Tab we will create new TabGroup with name **Samples**:

![Create new TabGroup](../../images/common/ribbon_customisation/new_tabgroup_en.png)

In left part of form select UserAction row in the list to see available options:

![Action List](../../images/common/ribbon_customisation/action_list_en.png)

After selecting our action **Run Sample** there is need to press button **Add >>** to add action to selected TabGroup:

![Added Action to TabGroup](../../images/common/ribbon_customisation/added_action_to_tabgroup_en.png)

In the end, you will see new Tab menu with new button:

![Updated Ribbon menu](../../images/common/ribbon_customisation/update_ribbon_menu_en.png)
