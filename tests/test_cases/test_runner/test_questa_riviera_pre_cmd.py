
import os
from cocotb.runner import get_runner

@cocotb.test()
def test_questa_riviera_pre_cmd(request, command):
    sim = os.getenv("SIM", "questa")

    dut = "test"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = "test"

    verilog_sources = ["test.sv"]

    pre_cmd = ['echo everything is fine!;']

    runner = get_runner(sim)
    runner.build(
        verilog_sources=verilog_sources,
        hdl_toplevel=toplevel,
        always=True,
    )
    runner.test(
        hdl_toplevel=toplevel,
        test_module=module,
        pre_cmd=pre_cmd,
    )
