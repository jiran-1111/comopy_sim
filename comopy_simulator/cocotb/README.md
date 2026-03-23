如果重新报错
```
Traceback (most recent call last):
  File "/home/ranrr/cocotb/comopy_simulator/test/run_test.py", line 11, in <module>
    from cocotb_tools.runner import get_runner
  File "/home/ranrr/cocotb/src/cocotb_tools/runner.py", line 39, in <module>
    import cocotb_tools.config
  File "/home/ranrr/cocotb/src/cocotb_tools/config.py", line 35, in <module>
    import cocotb
  File "/home/ranrr/cocotb/src/cocotb/__init__.py", line 11, in <module>
    from cocotb._decorators import parametrize, skipif, test, xfail
  File "/home/ranrr/cocotb/src/cocotb/_decorators.py", line 17, in <module>
    from cocotb.simtime import TimeUnit
  File "/home/ranrr/cocotb/src/cocotb/simtime.py", line 19, in <module>
    from cocotb import simulator
ImportError: cannot import name 'simulator' from partially initialized module 'cocotb' (most likely due to a circular import) (/home/ranrr/cocotb/src/cocotb/__init__.py)
```
要在根目录下重新安装一下

pip install -e .