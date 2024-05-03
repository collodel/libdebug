#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from libdebug.state.thread_context import ThreadContext

from libdebug.qemu_stub.qemu_abstract_register_holder import QemuRegisterHolder


class QemuGenericRegisterHolder(QemuRegisterHolder):
    """A class that holds the state of the registers of a process for a generic architecture, specifically for the `qemu` debugging backend."""

    def apply_on(self, target: "ThreadContext", target_class: type["ThreadContext"]):
        target.regs = self.register_file

        endianness = self.endianness

        if hasattr(target_class, self.register_definitions[0].name):
            return

        for definition in self.register_definitions:
            name, offset, size = definition.name, definition.offset, definition.size

            def get_property_for_reg(name, offset, size, endianness):
                def getter(self):
                    return int.from_bytes(
                        self.regs.internal_representation[offset : offset + size],
                        byteorder=endianness,
                    )

                def setter(self, value):
                    self.regs.internal_representation = (
                        self.regs.internal_representation[:offset]
                        + value.to_bytes(size, byteorder=endianness)
                        + self.regs.internal_representation[offset + size :]
                    )
                    self.regs.changed = True

                return property(getter, setter, None, name)

            setattr(
                target_class, name, get_property_for_reg(name, offset, size, endianness)
            )

        # Heuristics for various architectures
        if hasattr(target_class, "rip"):  # x86_64
            setattr(
                target_class,
                "instruction_pointer",
                property(
                    lambda self: self.rip,
                    lambda self, value: setattr(self, "rip", value),
                    None,
                    "instruction_pointer",
                ),
            )
        elif hasattr(target_class, "eip"):
            setattr(
                target_class,
                "instruction_pointer",
                property(
                    lambda self: self.eip,
                    lambda self, value: setattr(self, "eip", value),
                    None,
                    "instruction_pointer",
                ),
            )
        elif hasattr(target_class, "pc"):
            setattr(
                target_class,
                "instruction_pointer",
                property(
                    lambda self: self.pc,
                    lambda self, value: setattr(self, "pc", value),
                    None,
                    "instruction_pointer",
                ),
            )
        else:
            raise NotImplementedError(
                "Cannot find the instruction pointer register for this architecture."
            )