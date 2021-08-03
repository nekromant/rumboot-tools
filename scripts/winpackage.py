import os
import shutil
import glob 
import sys 
import zipfile
from rumboot import __version__

major = sys.version_info.major
minor = sys.version_info.minor
micro = sys.version_info.micro

packagedir=f"rumboot-tools-{__version__}-python{major}.{minor}.{micro}"

if os.path.exists(packagedir):
    print("Cleaning up...")
    shutil.rmtree(packagedir)
os.mkdir(packagedir)
os.mkdir(f"{packagedir}\wheelhouse")

print("Building windows packages...")
os.system("pip wheel .")

script = open(f"{packagedir}/install_system.cmd", "w+")
script.write("@echo off\n\r")
wheels = glob.glob("*.whl")
for f in wheels:
    os.rename(f, f"{packagedir}\wheelhouse\\{f}")
    script.write(f"pip install --no-index --no-deps wheelhouse\\{f}\n\r")
script.close()

script = open(f"{packagedir}/install_venv.cmd", "w+")
script.write("@echo off\n\r")
script.write("python -m venv venv\n\r")
script.write("venv\\Scripts\\activate.bat\n\r")
script.write("install_system.cmd\n\r")
script.write("echo rumboot-tools are installed into a virtual environment\n\r")
script.write("echo add venv\\Scripts to your $PATH to use them directly\n\r")
script.close()

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))
      
zipf = zipfile.ZipFile(f'{packagedir}.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(packagedir, zipf)
zipf.close()

print(f"Built  {packagedir}")
