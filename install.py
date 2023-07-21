import os
import sys
import pathlib
import apm.path


# move to the directory that __file__ is in.
os.chdir(pathlib.Path(__file__).parent)

# Warn the user of their impending 'device is full' error due to bloat
print("Installing dependencies using Poetry (sorry for the dependency)...")


def install_pip_dependency(*args: str) -> int:
    # Check if we are running on Gentoo (package manager is portage)
    on_gentoo = os.path.exists("/etc/portage")

    # The '--user' flag installs the package for the current user only
    # (non-system-wide).  '--user' is necessary to prevent breaking
    # Portage's python installation

    user_flag = " --user" if on_gentoo else ""

    return os.system(
        f"python3 -m pip install{user_flag} {' '.join(args)}"
    )  # nosec


# Check if poetry is installed, if not, install it.  Poetry is needed
# for install the dependencies of APM itself
try:
    import poetry

    del poetry

except ImportError:
    install_pip_dependency("poetry")


# Install dependencies with Poetry.
os.system("poetry install --no-root --without=dev")  # nosec


# Try importing 'kazparse' module; if it fails, install it from GitHub
# repository
try:
    import kazparse

    del kazparse

except ImportError:
    # Install 'kazparse' from the GitHub repository using 'pip'
    install_pip_dependency("git+https://github.com/R2Boyo25/cliparse.git")


print("Installing APM using the downloaded APM...")

# Run the 'apm' module with the arguments passed in the script's
# command line (sys.argv)
result = os.system(
    f"python3 -m apm {' '.join(sys.argv[1:])} install ."
)  # nosec

if result:
    # If the installation failed, print an error message and exit the
    # script with the result code
    print("Failed to install APM.")
    exit(result)

print(
    f"""Done.
It is now safe to delete the AvalonPackageManager\n\
folder you have just downloaded,
as it has been downloaded and installed\n\
to Avalon's directory - {apm.path.paths['root']}."""
)
