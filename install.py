# Import necessary modules
import os, sys

# Print a message to indicate the start of the script
print("Install dependencies.....")

# Install required dependencies from the 'requirements.txt' file using 'pip'
# The '--user' flag installs the packages for the current user only (non-system-wide)
# The condition checks if the system is Gentoo (package manager is portage) and if so, installs without '--user'
os.system(
    f"python3 -m pip install{' --user' if os.path.exists('/etc/portage') else ''} -r requirements.txt"
)

# Try importing 'kazparse' module; if it fails, install it from GitHub repository
try:
    import kazparse  # type: ignore
except:
    # Install 'kazparse' from the GitHub repository using 'pip'
    # The '--user' flag installs the package for the current user only (non-system-wide)
    # The condition checks if the system is Gentoo (package manager is portage) and if so, installs without '--user'
    os.system(
        f"python3 -m pip install{' --user' if os.path.exists('/etc/portage') else ''} git+https://github.com/R2Boyo25/cliparse.git"
    )

# Print a message to indicate the start of installing APM (Avalon Package Manager) using APM
print("Installing APM using APM...")

# Run the 'apm' command to install APM with the arguments passed in the script's command line (sys.argv)
# This assumes that 'apm' is an executable Python script that handles the installation process
result = os.system(f"python3 -m apm {' '.join(sys.argv[1:])} install .")

# Check if the installation was successful by inspecting the result value
if result:
    # If the installation failed (non-zero result code), print an error message and exit the script with the result code
    print("Failed to install APM.")
    exit(result)

# Print a message indicating the successful installation of APM
print(
    """Done.
It is now safe to delete the AvalonPackageManager folder you have just downloaded, 
as it has been downloaded and installed to Avalon's directory."""
)
