from brian2 import (Clock, Network, ms, second, BrianObject, defaultclock,
                    run, stop, NetworkOperation, network_operation,
                    restore_initial_state)
import copy
from numpy.testing import assert_equal, assert_raises
from nose import with_setup

@with_setup(teardown=restore_initial_state)
def test_empty_network():
    # Check that an empty network functions correctly
    net = Network()
    net.run(1*second)

class Counter(BrianObject):
    def __init__(self, **kwds):
        super(Counter, self).__init__(**kwds)
        self.count = 0        
    def update(self):
        self.count += 1

@with_setup(teardown=restore_initial_state)
def test_network_single_object():
    # Check that a network with a single object functions correctly
    x = Counter()
    net = Network(x)
    net.run(1*ms)
    assert_equal(x.count, 10)

@with_setup(teardown=restore_initial_state)
def test_network_two_objects():
    # Check that a network with two objects and the same clock function correctly
    x = Counter(order=5)
    y = Counter(order=6)
    net = Network()
    net.add([x, [y]]) # check that a funky way of adding objects work correctly
    assert_equal(net.objects[0].order, 5)
    assert_equal(net.objects[1].order, 6)
    assert_equal(len(net.objects), 2)
    net.run(1*ms)
    assert_equal(x.count, 10)
    assert_equal(y.count, 10)

updates = []
class Updater(BrianObject):
    def __init__(self, name, **kwds):
        super(Updater, self).__init__(**kwds)
        self.name = name
    def update(self):
        updates.append(self.name)

@with_setup(teardown=restore_initial_state)
def test_network_different_clocks():
    # Check that a network with two different clocks functions correctly
    clock1 = Clock(dt=1*ms, order=0)
    clock3 = Clock(dt=3*ms, order=1)
    x = Updater('x', clock=clock1)
    y = Updater('y', clock=clock3)
    net = Network(x, y)
    net.run(10*ms)
    assert_equal(''.join(updates), 'xyxxxyxxxyxxxy')

@with_setup(teardown=restore_initial_state)
def test_network_different_when():
    # Check that a network with different when attributes functions correctly
    updates[:] = []
    x = Updater('x', when='start')
    y = Updater('y', when='end')
    net = Network(x, y)
    net.run(0.3*ms)
    assert_equal(''.join(updates), 'xyxyxy')

class Preparer(BrianObject):
    def __init__(self, **kwds):
        super(Preparer, self).__init__(**kwds)
        self.did_reinit = False
        self.did_prepare = False
    def reinit(self):
        self.did_reinit = True
    def prepare(self):
        self.did_prepare = True
    def update(self):
        pass

@with_setup(teardown=restore_initial_state)
def test_network_reinit_prepare():
    # Check that reinit and prepare work        
    x = Preparer()
    net = Network(x)
    assert_equal(x.did_reinit, False)
    assert_equal(x.did_prepare, False)
    net.run(1*ms)
    assert_equal(x.did_reinit, False)
    assert_equal(x.did_prepare, True)
    net.reinit()
    assert_equal(x.did_reinit, True)

@with_setup(teardown=restore_initial_state)
def test_magic_network():
    # test that magic network functions correctly
    x = Counter()
    y = Counter()
    run(10*ms)
    assert_equal(x.count, 100)
    assert_equal(y.count, 100)

class Stopper(BrianObject):
    def __init__(self, stoptime, stopfunc, **kwds):
        super(Stopper, self).__init__(**kwds)
        self.stoptime = stoptime
        self.stopfunc = stopfunc
    
    def update(self):
        self.stoptime -= 1
        if self.stoptime<=0:
            self.stopfunc()

@with_setup(teardown=restore_initial_state)
def test_network_stop():
    # test that Network.stop and global stop() work correctly
    net = Network()
    x = Stopper(10, net.stop)
    net.add(x)
    net.run(10*ms)
    assert_equal(defaultclock.t, 1*ms)
    
    del net
    defaultclock.t = 0*second
    
    x = Stopper(10, stop)
    net = Network(x)
    net.run(10*ms)
    assert_equal(defaultclock.t, 1*ms)

@with_setup(teardown=restore_initial_state)
def test_network_operations():
    # test NetworkOperation and network_operation
    seq = []
    def f1():
        seq.append('a')
    op1 = NetworkOperation(f1, when='start')
    @network_operation
    def f2():
        seq.append('b')
    @network_operation(when='end', order=1)
    def f3():
        seq.append('c')
    run(1*ms)
    assert_equal(''.join(seq), 'abc'*10)

@with_setup(teardown=restore_initial_state)
def test_network_active_flag():
    # test that the BrianObject.active flag is recognised by Network.run
    x = Counter()
    y = Counter()
    y.active = False
    run(1*ms)
    assert_equal(x.count, 10)
    assert_equal(y.count, 0)

@with_setup(teardown=restore_initial_state)
def test_network_t():
    # test that Network.t works as expected
    c1 = Clock(dt=1*ms)
    c2 = Clock(dt=2*ms)
    x = Counter(clock=c1)
    y = Counter(clock=c2)
    net = Network(x, y)
    net.run(4*ms)
    assert_equal(c1.t, 4*ms)
    assert_equal(c2.t, 4*ms)
    assert_equal(net.t, 4*ms)
    net.run(1*ms)
    assert_equal(c1.t, 5*ms)
    assert_equal(c2.t, 6*ms)
    assert_equal(net.t, 5*ms)
    assert_equal(x.count, 5)
    assert_equal(y.count, 3)
    net.run(0.5*ms) # should only update x
    assert_equal(c1.t, 6*ms)
    assert_equal(c2.t, 6*ms)
    assert_equal(net.t, 5.5*ms)
    assert_equal(x.count, 6)
    assert_equal(y.count, 3)
    net.run(0.5*ms) # shouldn't do anything
    assert_equal(c1.t, 6*ms)
    assert_equal(c2.t, 6*ms)
    assert_equal(net.t, 6*ms)
    assert_equal(x.count, 6)
    assert_equal(y.count, 3)
    net.run(0.5*ms) # should update x and y
    assert_equal(c1.t, 7*ms)
    assert_equal(c2.t, 8*ms)
    assert_equal(net.t, 6.5*ms)
    assert_equal(x.count, 7)
    assert_equal(y.count, 4)
    
    del c1, c2, x, y, net

    # now test with magic run    
    c1 = Clock(dt=1*ms)
    c2 = Clock(dt=2*ms)
    x = Counter(clock=c1)
    y = Counter(clock=c2)
    run(4*ms)
    assert_equal(c1.t, 4*ms)
    assert_equal(c2.t, 4*ms)
    assert_equal(x.count, 4)
    assert_equal(y.count, 2)
    run(4*ms)
    assert_equal(c1.t, 8*ms)
    assert_equal(c2.t, 8*ms)
    assert_equal(x.count, 8)
    assert_equal(y.count, 4)
    run(1*ms)
    assert_equal(c1.t, 9*ms)
    assert_equal(c2.t, 10*ms)
    assert_equal(x.count, 9)
    assert_equal(y.count, 5)
    
@with_setup(teardown=restore_initial_state)
def test_network_remove():
    x = Counter()
    y = Counter()
    net = Network(x, y)
    net.remove(y)
    net.run(1*ms)
    assert_equal(x.count, 10)
    assert_equal(y.count, 0)
    # the relevance of this test is when we use weakref.proxy objects in
    # Network.objects, we should be able to add and remove these from
    # the Network just as much as the original objects
    for obj in copy.copy(net.objects):
        net.remove(obj)
    net.run(1*ms)
    assert_equal(x.count, 10)
    assert_equal(y.count, 0)

@with_setup(teardown=restore_initial_state)
def test_network_copy():
    x = Counter()
    net = Network(x)
    net2 = Network()
    for obj in net.objects:
        net2.add(obj)
    net2.run(1*ms)
    assert_equal(x.count, 10)
    net.run(1*ms)
    assert_equal(x.count, 20)


if __name__=='__main__':
    for t in [test_empty_network,
              test_network_single_object,
              test_network_two_objects,
              test_network_different_clocks,
              test_network_different_when,
              test_network_reinit_prepare,
              test_magic_network,
              test_network_stop,
              test_network_operations,
              test_network_active_flag,
              test_network_t,
              test_network_remove,
              test_network_copy,
              ]:
        t()
        restore_initial_state()