from rumboot.ops.base import base

# HINT: most exits are handled in xmodem class, since 
# this is also the place for incremental uploads
class termination(base):
    formats = {
        "panic" : "PANIC: {}",
        }

    def action(self, trigger, result):
        if trigger == "panic":
            return -1
