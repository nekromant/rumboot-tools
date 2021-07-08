import time
import os


class RumbootTestBase:
    timeout = 5 * 60
    requested = {} # { "param1": "value1", "param2": "value2", { ... } } is compared with the environment

    def _suitable(req, env):
        for key, value in req.items():
            if not key in env:
                return False
            if isinstance(value, dict):
                if not isinstance(env[key], dict):
                    return False
                return RumbootTestBase._suitable(value, env[key])
            if value != env[key]:
                return False
        return True

    @classmethod
    def suitable(self, env, params):
        return RumbootTestBase._suitable(self.requested, env)

    # ??? temporary -> terminal
    def write_command(self, cmd):
        cmd = cmd.encode() + b"\r"
        self.terminal.ser.write(cmd)

    def __init__(self, terminal, resetSeq, env, params, user_interaction):
        self.terminal = terminal
        self.resetSeq = resetSeq
        self.env = env
        self.params = params
        self.user_interaction = user_interaction

    def run(self):
        self.resetSeq.resetToHost()
        time.sleep(5) # Ethernet PHY negotiation time for EDCL loading (ToDo: move to EDCL part)
        return True


class UBootTestBase(RumbootTestBase):

    @classmethod
    def suitable(self, env, params):
        if not super(UBootTestBase, self).suitable(env, params):
            return False
        if not "uboot" in env:
            return False
        if not env["uboot"].get("active", False):
            return False
        return True

    def mem_setup(self):
        mem_setup_cmd = self.env["uboot"].get("mem_setup_cmd")
        if mem_setup_cmd != None:
            self.terminal.shell_cmd(mem_setup_cmd)

    def uboot_upload_file(self, addr_as_text, file_path):
        transport = self.env["connection"]["transport"]
        if (transport == "edcl"):
            self.write_command(f"echo UPLOAD to {addr_as_text}. \\\'X\\\' for X-modem, \\\'E\\\' for EDCL")
            self.terminal.add_binaries(file_path)
            self.terminal.loop(False, True)
            self.terminal.wait_prompt()
            self.terminal.ser.write(b"\b") # ??? -> terminal clear E character
# ???         elif (transport == "xmodem"):
# ???             self.hardware.write_command(f"loadx {addr_as_text}")
# ???             self.hardware.load_binaries([file_path])
# ???             self.hardware.wait_shell_prompt()
# ???         else:
# ???             raise "Unsupported transport"

    def run(self):
        super().run()

        binaries = []
        if "spl_path" in self.env["uboot"]:
            binaries.append(os.path.join(self.env["root_path"], self.env["uboot"]["path_base"], self.env["uboot"]["spl_path"]))
        if "uboot_path" in self.env["uboot"]:
            binaries.append(os.path.join(self.env["root_path"], self.env["uboot"]["path_base"], self.env["uboot"]["uboot_path"]))
        for file in binaries:
            self.terminal.add_binaries(file)

        self.terminal.loop(False, True)
        self.terminal.shell_mode("=> ")
        self.terminal.wait_prompt()

        return True


class KernelTestBase(UBootTestBase):

    @classmethod
    def suitable(self, env, params):
        if not super(KernelTestBase, self).suitable(env, params):
            return False
        if not "kernel" in env:
            return False
        if not env["kernel"].get("active", False):
            return False
        return True

    def run(self):
        super().run()
        self.mem_setup()

        if "bootargs" in self.env["kernel"]:
            self.terminal.shell_cmd(f"setenv bootargs {self.env['kernel']['bootargs']}")

        uimage_path = os.path.join(self.env["root_path"], self.env["kernel"]["path_base"], self.env["kernel"]["uimage_path"])
        self.uboot_upload_file("${loadaddr}", uimage_path)

        dtb_path = os.path.join(self.env["root_path"], self.env["kernel"]["path_base"], self.env["kernel"]["dtb_path"])
        self.uboot_upload_file("${fdt_addr_r}", dtb_path)

        self.write_command("bootm ${loadaddr} - ${fdt_addr_r}")
        self.terminal.wait("{} login:")
        self.write_command(self.env["kernel"]["user"])
        self.terminal.wait("Password:")
        self.write_command(self.env["kernel"]["password"])
        self.terminal.wait("{}#")

        self.write_command('A="=="; PS1="$A> "')
        self.terminal.shell_mode("==> ")
        self.terminal.wait_prompt()

        return True
