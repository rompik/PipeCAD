# Pipe Modeling
The data structure for pipe modeling is also hierarchical, as shown in the figure below:

![Pipe Hierarchy](images/design/design_pipe_tree_zh.png "Pipe Data Hierarchy")

## Creating a Pipe
Create a pipe by clicking the Pipeline->Create button on the PIPING panel. Enter the pipe Name, select the Spec, Bore, and design parameters.

![Create Pipe](images/design/design_pipe_create_zh.png "Create Pipe")

To modify a pipe, use the Pipeline->Modify button on the PIPING panel. Pipe modification includes creating and editing branches. Branch data mainly specifies the Head/Tail positions and connection relationships.

![Modify Pipe](images/design/design_pipe_modify_zh.png "Modify Pipe")

## Creating a Branch
Branch details include Head/Tail positions, direction, bore, and connection type. One way is to directly edit these data. If the head and tail are aligned and parallel, but with opposite directions, a pipe model will be generated. Otherwise, only a dashed line is shown.

The branch head and tail are marked with different shapes: the head is shown as an arrow with a handle, and the tail as an arrow without a handle. Another way to modify a branch is to specify the connected model, which can be another pipe, fitting, equipment, or nozzle. This can be interactively selected in the model for convenience.

## Creating Components
After creating the PIPE and BRANCH, the main function of pipe design is to arrange components such as flanges and valves. Since components are implemented parametrically, their creation requires connecting design data and the component library via the pipe spec. Component placement also involves positioning: components are modeled in a local coordinate system and must be transformed to the actual design position. Use the Create Component button on the PIPING panel to add components.

![Create Component](images/design/design_component_create_zh.png "Create Component")

Branch spec provides filtering by category, such as Elbow, Flange, Valve, etc., and further by Skey. Skey filtering helps users recognize component symbols on ISO drawings and avoids cluttered filtering types.

Adjust the position and orientation of components by rotating and moving them to complete the pipe model.
