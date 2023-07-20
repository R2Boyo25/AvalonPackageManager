import os, sys

print("Install dependencies.....")
os.system(
    f"python3 -m pip install{' --user' if os.path.exists('/etc/portage') else ''} -r requirements.txt"
)

try:
    import kazparse  # type: ignore
except:
    os.system(
        f"python3 -m pip install{' --user' if os.path.exists('/etc/portage') else ''} git+https://github.com/R2Boyo25/cliparse.git"
    )

print("Installing APM using APM...")
result = os.system(f"python3 -m apm {' '.join(sys.argv[1:])} install .")

if result:
    print("Failed to install APM.")
    exit(result)

print(
    """Done.
It is now safe to delete the AvalonPackageManager folder you have just downloaded, 
as it has been downloaded and installed to Avalon's directory."""
)
