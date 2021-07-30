import threading
import time
import os
import sys


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

    def __init__(self, name, full_name, terminal, reset_seq, env, params, user_interaction):
        self.name = name
        self.full_name = full_name
        self.terminal = terminal
        self.reset_seq = reset_seq
        self.env = env
        self.params = params
        self.user_interaction = user_interaction

    def run(self):
        try:
            self.reset_seq.resetToHost()
        except:
            print("WARN: Reset method doesn't support HOST mode switching")
            print("WARN: If things don't work - check jumpers!")
            self.reset_seq.reset()
        return True

    # UserInteraction
    def request_message(self, text):
        save_stdout = sys.stdout
        sys.stdout = sys.__stdout__
        threading.current_thread().wait_user = True
        try:
            self.user_interaction.request_message(self, text)
        finally:
            sys.stdout = save_stdout
            threading.current_thread.wait_user = False
        print(f"User interaction: {text}")

    # UserInteraction
    def request_yes_no(self, text):
        save_stdout = sys.stdout
        sys.stdout = sys.__stdout__
        threading.current_thread.wait_user = True
        try:
            result = self.user_interaction.request_yes_no(self, text)
        finally:
            sys.stdout = save_stdout
            threading.current_thread.wait_user = False
        answer = "YES" if result else "NO"
        print(f"User interaction: {text} - {answer}")
        return result

    # UserInteraction
    def request_option(self, text, options):
        save_stdout = sys.stdout
        sys.stdout = sys.__stdout__
        threading.current_thread.wait_user = True
        try:
            result = self.user_interaction.request_option(self, text, options)
        finally:
            sys.stdout = save_stdout
            threading.current_thread.wait_user = False
        answer = options[result]
        print(f"User interaction: {text} - {answer}")
        return result

    # ??? temporary -> terminal
    def write_command(self, cmd):
        cmd = cmd.encode() + b"\r"
        self.terminal.ser.write(cmd)


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

    def uboot_cmd_answer(self, cmd, last_line_answer):
        answer = self.terminal.shell_cmd(cmd)
        lines = answer.splitlines(keepends=False)
        last_line = "" if len(lines) == 0 else lines[-1]
        if last_line != last_line_answer:
            print(f"Expected answer: {last_line_answer}")
            print(f"Current answer: {last_line}")
            raise Exception("Unexpected answer")
        return True

    def mem_setup(self):
        mem_setup_cmd = self.env["uboot"].get("mem_setup_cmd")
        if mem_setup_cmd != None:
            self.terminal.shell_cmd(mem_setup_cmd)

    def mem_fill(self, addr, size, value):
        self.terminal.shell_cmd(f"mw.b {addr:X} {value:02X} {size:X}")

    def mem_random(self, addr, size):
        self.uboot_cmd_answer(f"rand {addr:X} {size:X}", f"{size} bytes filled with random data")

    def mem_cmp(self, addr1, addr2, size):
        self.uboot_cmd_answer(f"cmp.b {addr1:X} {addr2:X} {size:X}", f"Total of {size} byte(s) were the same")

    def uboot_upload_file(self, addr_as_text, file_path):
        transport = self.env["connection"]["transport"]
        if (transport == "edcl"):
            self.write_command(f"echo UPLOAD to {addr_as_text}. \\\'X\\\' for X-modem, \\\'E\\\' for EDCL")
            self.terminal.add_binaries(file_path)
            self.terminal.loop(False, True)
            self.terminal.wait_prompt()
            self.terminal.ser.write(b"\b") # ??? -> terminal clear E character
        elif (transport == "xmodem"):
            self.write_command(f"loadx {addr_as_text}")
            self.terminal.load_binaries(file_path)
        else:
            raise "Unsupported transport"

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
