from rumboot.ops.base import base

class termination(base):
    formats = {
        "panic" : "PANIC: {}",
        }

    def action(self, trigger, result):
        if trigger == "panic":
            return -1
