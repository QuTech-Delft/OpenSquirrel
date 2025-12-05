The [Qgym](https://github.com/QuTech-Delft/qgym) package functions in a manner similar 
to the well-known gym package, in the sense that it provides a number of environments 
on which reinforcement learning (RL) agents can be applied. 
The main purpose of qgym is to develop reinforcement learning environments which 
represent various passes of the [OpenQL framework](https://arxiv.org/abs/2005.13283).

The package offers RL-based environments resembling quantum compilation steps, namely 
for initial mapping, qubit routing, and gate scheduling. 
The environments offer all the relevant components needed to train agents, including 
states and action spaces, and (customizable) reward functions (basically all the 
components required by a Markov Decision Process). 
Furthermore, the actual training of the agents is handled by the 
[StableBaselines3](https://github.com/DLR-RM/stable-baselines3) python package, which 
offers reliable, customizable, out of the box Pytorch implementations of DRL agents.

The initial mapping problem is translated to a RL context within Qgym in the following 
manner. 
The setup begins with a fixed connection graph (an undirected graph representation of 
the hardware connectivity scheme), static across all episodes. 
Each episode introduces a novel, randomly generated interaction graph (undirected graph 
representation of the qubit interactions within the circuit) for the agent to observe, 
alongside an initially empty mapping. 
At every step, the agent can map a virtual (logical) qubit to a physical qubit until 
the mapping is fully established. 
In theory, this process enables the training of agents that are capable of managing 
various interaction graphs on a predetermined hardware layout. 
Both the interaction and connection graphs are easily represented via 
[Networkx](https://networkx.org/) graphs.

At the moment, the following DRL agents can be used to map circuits in Opensquirrel:

- Proximal Policy Optimization (PPO)
- Advantage Actor-Critic (A2C)
- Trust Region Policy Optimization (TRPO)
- Recurrent PPO
- PPO with illegal action masking

The last three agents in the above list can be imported from the extension/experimental 
package of StableBaselines3, namely [sb3-contrib](https://github.com/Stable-Baselines-Team/stable-baselines3-contrib). 

The following code snippet demonstrates the usage of the `QGymMapper`. Assume that you
have a `connectivities.json` file containing some hardware connectivity schemes, as 
well as a `TRPO.zip` file containing the weights of a trained agent in your working 
directory. 

```python
from opensquirrel.passes.mapper import QGymMapper
from opensquirrel import CircuitBuilder
import networkx as nx
import json

with open('connectivities.json', 'r') as file:
    connectivities = json.load(file)

hardware_connectivitiy = connectivities["tuna-5"]

connection_graph = nx.Graph()
connection_graph.add_edges_from(hardware_connectivity)

qgym_mapper = QGymMapper(agent_class = "TRPO", agent_path = "TRPO.zip", 
                        hardware_connectivity=connection_graph)

builder = CircuitBuilder(5)
builder.H(0)
builder.CNOT(0, 1)
builder.H(2)
builder.CNOT(1, 2)
builder.CNOT(2, 4)
builder.CNOT(3, 4)
circuit = builder.to_circuit()

circuit.map(mapper = qgym_mapper)
```