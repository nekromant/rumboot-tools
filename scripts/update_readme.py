import sys
import subprocess
braces_open=False
first_line = False
print_line = True

def get_some_help(cmd):
    cmd = cmd.split(" ")
    out = subprocess.Popen(cmd, 
           stdout=subprocess.PIPE, 
           stderr=subprocess.PIPE)
    stdout,stderr = out.communicate()
    return stdout

with open("README.md", "r") as f:
    for line in f:
        line = line.replace("\n", "")
        if line.strip() == "```":
            braces_open = not braces_open
            first_line = True
            if not braces_open:
                print_line = True
            print(line)
        else:
            if first_line and line.find("~#") >= 0 and line.find("--help") >= 0:
                cmd = line.replace("~#","").strip()
                print_line = False
                h = get_some_help(cmd)
                print(line)
                print(h.decode())
            if print_line:
                print(line)
            first_line = False


