import os, sys

print("Install dependencies.....")
os.system(f"pip3 install{' --user' if os.path.exists('/etc/portage') else ''} -r requirements.txt")

try: 
    import CLIParse
except:
    os.system(f"pip3 install{' --user' if os.path.exists('/etc/portage') else ''} git+https://github.com/R2Boyo25/CLIParse.git")

print("Installing APM using APM...")
os.system(f"python3 ./main.py install . {' '.join(sys.argv[1:])}")

print("Done.")
print("It is now safe to delete the AvalonPackageManager folder you have just downloaded, as it has been downloaded and installed to Avalon's directory.")
