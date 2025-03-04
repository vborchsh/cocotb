.. _writing_tbs:

*******************
Writing Testbenches
*******************


.. _writing_tbs_accessing_design:

Accessing the design
====================

When cocotb initializes it finds the toplevel instantiation in the simulator
and creates a *handle* called ``dut``. Toplevel signals can be accessed using the
"dot" notation used for accessing object attributes in Python. The same mechanism
can be used to access signals inside the design.

.. code-block:: python3

    # Get a reference to the "clk" signal on the toplevel
    clk = dut.clk

    # Get a reference to a register "count"
    # in a sub-block "inst_sub_block"
    # (the instance name of a Verilog module or VHDL entity/component)
    count = dut.inst_sub_block.count


.. _writing_tbs_finding_elements:

Finding elements in the design
==============================

To find elements of the DUT
(for example, instances, signals, or constants)
at a certain hierarchy level,
you can use the :func:`dir` function on a handle.

.. code-block:: python3

    # Print the instances and signals (which includes the ports) of the design's toplevel
    print(dir(dut))

    # Print the instances and signals of "inst_sub_block" under the toplevel
    # which is the instance name of a Verilog module or VHDL entity/component
    print(dir(dut.inst_sub_block))


.. _writing_tbs_assigning_values:

Assigning values to signals
===========================

Values can be assigned to signals using either the
:attr:`~cocotb.handle.NonHierarchyObject.value` property of a handle object
or using direct assignment while traversing the hierarchy.

.. code-block:: python3

    # Get a reference to the "clk" signal and assign a value
    clk = dut.clk
    clk.value = 1

    # Direct assignment through the hierarchy
    dut.input_signal.value = 12

    # Assign a value to a memory deeper in the hierarchy
    # ("inst_sub_block" and "inst_memory" are instance names of the
    # respective Verilog modules or VHDL entity/components in the DUT)
    dut.inst_sub_block.inst_memory.mem_array[4].value = 2


The assignment syntax ``sig.value = new_value`` has the same semantics as :term:`HDL`:
writes are not applied immediately, but delayed until the next write cycle.
Use ``sig.setimmediatevalue(new_val)`` to set a new value immediately
(see :meth:`~cocotb.handle.NonHierarchyObject.setimmediatevalue`).

.. _writing_tbs_assigning_values_signed_unsigned:

Signed and unsigned values
--------------------------

Both signed and unsigned values can be assigned to signals using a Python int.
Cocotb makes no assumptions regarding the signedness of the signal. It only
considers the width of the signal, so it will allow values in the range from
the minimum negative value for a signed number up to the maximum positive
value for an unsigned number: ``-2**(Nbits - 1) <= value <= 2**Nbits - 1``
Note: assigning out-of-range values will raise an :exc:`OverflowError`.

A :class:`BinaryValue` object can be used instead of a Python int to assign a
value to signals with more fine-grained control (e.g. signed values only).

.. code-block:: verilog

    module my_module (
        input   logic       clk,
        input   logic       rst,
        input   logic [2:0] data_in,
        output  logic [2:0] data_out
        );

.. code-block:: python3

    # assignment of negative value
    dut.data_in.value = -4

    # assignment of positive value
    dut.data_in.value = 7

    # assignment of out-of-range values
    dut.data_in.value = 8   # raises OverflowError
    dut.data_in.value = -5  # raises OverflowError


.. _writing_tbs_reading_values:

Reading values from signals
===========================

Values in the DUT can be accessed with the :attr:`~cocotb.handle.NonHierarchyObject.value`
property of a handle object.
A common mistake is forgetting the ``.value`` which just gives you a reference to a handle
(useful for defining an alias name), not the value.

The Python type of a value depends on the handle's HDL type:

* Arrays of ``logic`` and subtypes of that (``sfixed``, ``unsigned``, etc.)
  are of type :class:`~cocotb.binary.BinaryValue`.
* Integer nets and constants (``integer``, ``natural``, etc.) return :class:`int`.
* Floating point nets and constants (``real``) return :class:`float`.
* Boolean nets and constants (``boolean``) return :class:`bool`.
* String nets and constants (``string``) return :class:`bytes`.

For a :class:`~cocotb.binary.BinaryValue` object, any unresolved bits are preserved and
can be accessed using the :attr:`~cocotb.binary.BinaryValue.binstr` attribute,
or a resolved integer value can be accessed using the :attr:`~cocotb.binary.BinaryValue.integer` attribute.

.. code-block:: pycon

    >>> # Read a value back from the DUT
    >>> count = dut.counter.value
    >>> print(count.binstr)
    1X1010
    >>> # Resolve the value to an integer (X or Z treated as 0)
    >>> print(count.integer)
    42
    >>> # Show number of bits in a value
    >>> print(count.n_bits)
    6

We can also cast the signal handle directly to an integer:

.. code-block:: pycon

    >>> print(int(dut.counter))
    42


.. _writing_tbs_identifying_tests:

Identifying tests
=================

Cocotb tests are identified using the :class:`~cocotb.test` decorator.
Using this decorator will tell cocotb that this function is a special type of coroutine that is meant
to either pass or fail.
The :class:`~cocotb.test` decorator supports several keyword arguments (see section :ref:`writing-tests`).
In most cases no arguments are passed to the decorator so cocotb tests can be written as:

.. code-block:: python3

    # A valid cocotb test
    @cocotb.test
    async def test(dut):
        pass

    # Also a valid cocotb test
    @cocotb.test()
    async def test(dut):
        pass

.. _writing_tbs_concurrent_sequential:

Concurrent and sequential execution
===================================

An :keyword:`await` will run an :keyword:`async` coroutine and wait for it to complete.
The called coroutine "blocks" the execution of the current coroutine.
Wrapping the call in :func:`~cocotb.start` or :func:`~cocotb.start_soon` runs the coroutine concurrently,
allowing the current coroutine to continue executing.
At any time you can :keyword:`await` the result of a :class:`~cocotb.Task`,
which will block the current coroutine's execution until the task finishes.

The following example shows these in action:

.. code-block:: python3

    # A coroutine
    async def reset_dut(reset_n, duration_ns):
        reset_n.value = 0
        await Timer(duration_ns, units="ns")
        reset_n.value = 1
        reset_n._log.debug("Reset complete")

    @cocotb.test()
    async def parallel_example(dut):
        reset_n = dut.reset

        # Execution will block until reset_dut has completed
        await reset_dut(reset_n, 500)
        dut._log.debug("After reset")

        # Run reset_dut concurrently
        reset_thread = cocotb.start_soon(reset_dut(reset_n, duration_ns=500))

        # This timer will complete before the timer in the concurrently executing "reset_thread"
        await Timer(250, units="ns")
        dut._log.debug("During reset (reset_n = %s)" % reset_n.value)

        # Wait for the other thread to complete
        await reset_thread
        dut._log.debug("After reset")

See :ref:`coroutines` for more examples of what can be done with coroutines.


.. _writing_tbs_assigning_values_forcing_freezing:

Forcing and freezing signals
============================

In addition to regular value assignments (deposits), signals can be forced
to a predetermined value or frozen at their current value. To achieve this,
the various actions described in :ref:`assignment-methods` can be used.

.. code-block:: python3

    # Deposit action
    dut.my_signal.value = 12
    dut.my_signal.value = Deposit(12)  # equivalent syntax

    # Force action
    dut.my_signal.value = Force(12)    # my_signal stays 12 until released

    # Release action
    dut.my_signal.value = Release()    # Reverts any force/freeze assignments

    # Freeze action
    dut.my_signal.value = Freeze()     # my_signal stays at current value until released


.. _writing_tbs_accessing_underscore_identifiers:

Accessing Identifiers Starting with an Underscore
=================================================

The attribute syntax of ``dut._some_signal`` cannot be used to access
an identifier that starts with an underscore (``_``, as is valid in Verilog)
because we reserve such names for cocotb-internals,
thus the access will raise an :exc:`AttributeError`.

A workaround is to use indirect access using
:meth:`~cocotb.handle.HierarchyObject._id` like in the following example:
``dut._id("_some_signal", extended=False)``.


Passing and Failing Tests
=========================

A cocotb test is considered to have `failed` if the test coroutine or any running :class:`~cocotb.Task`
fails an ``assert`` statement.
Below are examples of `failing` tests.

.. code-block:: python3

    @cocotb.test()
    async def test(dut):
        assert 1 > 2, "Testing the obvious"

    @cocotb.test()
    async def test(dut):
        async def fails_test():
            assert 1 > 2
        cocotb.start_soon(fails_test())
        await Timer(10, 'ns')

When a test fails, a stacktrace is printed.
If :mod:`pytest` is installed and ``assert`` statements are used,
a more informative stacktrace is printed which includes the values that caused the ``assert`` to fail.
For example, see the output for the first test from above.

.. code-block::

    0.00ns ERROR    Test Failed: test (result was AssertionError)
                    Traceback (most recent call last):
                      File "test.py", line 3, in test
                        assert 1 > 2, "Testing the obvious"
                    AssertionError: Testing the obvious


A cocotb test is considered to have `errored` if the test coroutine or any running :class:`~cocotb.Task`
raises an exception that isn't considered a `failure`.
Below are examples of `erroring` tests.

.. code-block:: python3

    @cocotb.test()
    async def test(dut):
        await coro_that_does_not_exist()  # NameError

    @cocotb.test()
    async def test(dut):
        async def coro_with_an_error():
            dut.signal_that_does_not_exist.value = 1  # AttributeError
        cocotb.start_soon(coro_with_an_error())
        await Timer(10, 'ns')

When a test ends with an error, a stacktrace is printed.
For example, see the below output for the first test from above.

.. code-block::

    0.00ns ERROR    Test Failed: test (result was NameError)
                    Traceback (most recent call last):
                      File "test.py", line 3, in test
                        await coro_that_does_not_exist()  # NameError
                    NameError: name 'coro_that_does_not_exist' is not defined


If a test coroutine completes without `failing` or `erroring`,
or if the test coroutine or any running :class:`~cocotb.Task`
raises :exc:`cocotb.result.TestSuccess`,
the test is considered to have `passed`.
Below are examples of `passing` tests.

.. code-block:: python3

    @cocotb.test():
    async def test(dut):
        assert 2 > 1  # assertion is correct, then the coroutine ends

    @cocotb.test()
    async def test(dut):
        raise TestSuccess("Reason")  # ends test with success early
        assert 1 > 2  # this would fail, but it isn't run because the test was ended early

    @cocotb.test()
    async def test(dut):
        async def ends_test_with_pass():
            raise TestSuccess("Reason")
        cocotb.start_soon(ends_test_with_pass())
        await Timer(10, 'ns')

A passing test will print the following output.

.. code-block::

    0.00ns INFO     Test Passed: test


Logging
=======

Cocotb uses the builtin :mod:`logging` library, with some configuration described in :ref:`logging-reference-section` to provide some sensible defaults.
All :class:`~cocotb.Task`\ s have a :class:`logging.Logger`,
and can be set to its own logging level.

.. code-block:: python3

    task = cocotb.start_soon(coro)
    task.log.setLevel(logging.DEBUG)
    task.log.debug("Running Task!")

The :term:`DUT` and each hierarchical object can also have individual logging levels set.
When logging :term:`HDL` objects, beware that ``_log`` is the preferred way to use
logging. This helps minimize the change of name collisions with an :term:`HDL` log
component with the Python logging functionality.

.. code-block:: python3

    dut.my_signal._log.info("Setting signal")
    dut.my_signal.value = 1
