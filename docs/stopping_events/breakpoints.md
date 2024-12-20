---
icon: material/sign-caution
search:
    boost: 4
---
# :material-sign-caution: Breakpoints
Breakpoints are the killer feature of any debugger, the fundamental stopping event. They allow you to stop the execution of your code at a specific point and inspect the state of your program to find bugs or understand its design.

!!! WARNING "Multithreading and Breakpoints"
    **libdebug** breakpoints are shared across all threads. This means that any thread can hit the breakpoint and cause the process to stop. You can use the [`hit_on()`](../debugging_flow/#hit-records) method of a breakpoint object to determine which thread hit the breakpoint (provided that the stop was indeed caused by the breakpoint).

A breakpoint can be inserted at any of two levels: *software* or *hardware*.

### :octicons-code-24: Software Breakpoints
Software breakpoints in the Linux kernel are implemented by patching the code in memory at runtime. The instruction at the chosen address is replaced with an interrupt instruction that is conventionally used for debugging. For example, in the `i386` and `AMD64` instruction sets, `int3` (0xCC) is reserved for this purpose.

When the `int3` instruction is executed, the CPU raises a `SIGTRAP` signal, which is caught by the debugger. The debugger then stops the process and restores the original instruction to its rightful place.

!!! TIP "Pros and Cons of Software Breakpoints"
    Software breakpoints are unlimited, but they can break when the program uses self-modifying code. This is because the patched code could be overwritten by the program. On the other hand, software breakpoints are slower than their hardware counterparts on most modern CPUs.

### :octicons-cpu-24: Hardware Breakpoints
Hardware breakpoints are a more reliable way to set breakpoints. They are made possible by the existence of special registers in the CPU that can be used to monitor memory accesses. Differently from software breakpoints, their hardware counterparts allows the debugger to monitor read and write accesses on top of code execution. This kind of hardware breakpoint is also called a [watchpoint](../watchpoints). More information on watchpoints can be found in the dedicated documentation.

!!! TIP "Pros and Cons of Hardware Breakpoints"
    Hardware breakpoints are not affected by self-modifying code. They are also usually faster and more flexible. However, hardware breakpoints are limited in number and are hardware-dependent, so their support may vary across different systems.

!!! INFO "Hardware Breakpoint Alignment in AArch64"
    Hardware breakpoints have to be aligned to 4 bytes (which is the size of an ARM instruction).


## **libdebug** API for Breakpoints

The `breakpoint()` function in the [Debugger](../../from_pydoc/generated/debugger/debugger/) object sets a breakpoint at a specific address.

!!! ABSTRACT "Function Signature"
    ```python
    d.breakpoint(position, hardware=False, condition='x', length=1, callback=None, file='hybrid')
    ```

**Parameters**:

| Argument | Type | Description |
| --- | --- | --- |
| `position` | `int` \| `str` | The address or symbol where the breakpoint will be set. |
| `hardware` | `bool` | Set to `True` to set a hardware breakpoint. |
| `condition` | `str` | The type of access in case of a hardware breakpoint. |
| `length` | `int` | The size of the word being watched in case of a hardware breakpoint. |
| `callback` | `Callable` \| `bool` (see callback signature [here](#callback-signature)) | Used to create asyncronous breakpoints (read more on the [debugging flow of stopping events](../debugging_flow)). |
| `file` | `str` | The backing file for relative addressing. Refer to the [memory access](../../basics/memory_access/#absolute-and-relative-addressing) section for more information on addressing modes. |

**Returns**:

| Return | Type | Description |
| --- | --- | --- |
| `Breakpoint` | [Breakpoint](../../from_pydoc/generated/data/breakpoint) | The breakpoint object created. |

!!! WARNING "Limited Hardware Breakpoints"
    Hardware breakpoints are limited in number. If you exceed the number of hardware breakpoints available on your system, a `RuntimeError` will be raised.

---

!!! ABSTRACT "Usage Example"
    ```python
    from libdebug import debugger

    d = debugger("./test_program")

    d.run()

    bp = d.breakpoint(0x10ab, file="binary") # (1)
    bp1 = d.breakpoint("main", file="binary") # (3)
    bp2 = d.breakpoint("printf", file="libc") # (4)

    d.cont()

    print(f"RAX: {d.regs.rax} at the breakpoint") # (2)
    if bp.hit_on(d):
        print("Breakpoint at 0x10ab was hit")
    elif bp1.hit_on(d):
        print("Breakpoint at main was hit")
    elif bp2.hit_on(d):
        print("Breakpoint at printf was hit")
    ```

    1. Set a software breakpoint at address 0x10ab relative to the program's base address
    2. Print the value of the RAX register when the breakpoint is hit
    3. Set a software breakpoint at the `main` symbol
    4. Set a software breakpoint at the `printf` symbol in the `libc` library


### Callback Signature
If you wish to create an [asynchronous](../debugging_flow) breakpoint, you will have to provide a callback function. If you want to leave the callback empty, you can set callback to `True`.

!!! ABSTRACT "Callback Signature"
    ```python
    def callback(t: ThreadContext, bp: Breakpoint):
    ```

**Parameters**:

| Argument | Type | Description |
| --- | --- | --- |
| `t` | [ThreadContext](../../from_pydoc/generated/state/thread_context) | The thread that hit the breakpoint. |
| `bp` | [Breakpoint](../../from_pydoc/generated/data/breakpoint) | The breakpoint object that triggered the callback. |

---

!!! ABSTRACT "Example usage of asynchronous breakpoints"
    ```python
    def on_breakpoint_hit(t, bp):
        print(f"RAX: {t.regs.rax}")

        if bp.hit_count == 100:
            print("Hit count reached 100")
            bp.disable()

    d.breakpoint(0x11f0, callback=on_breakpoint_hit, file="binary")
    ```
