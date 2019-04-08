'''
Network Operation Example:
    Change the threshold of a neuron every 50 ms with use of 
    network operation
'''

import numpy as np
from brian2 import (plot, network_operation, ms, show, NeuronGroup,
                    StateMonitor, run, xlabel, ylabel)

tau = 10*ms
eqs = '''
dv/dt = (1-v)/tau : 1
vt : 1
'''

G = NeuronGroup(1, eqs, threshold='v>vt', reset='v = 0', method='exact')
G.vt = 0.8


@network_operation(dt=50*ms)
def update_threshold():
    G.vt = np.random.uniform(low=0, high=1)


M = StateMonitor(G, 'v', record=0)
run(200*ms)
plot(M.t/ms, M.v[0])
xlabel('Time (ms)')
ylabel('v')
show()
