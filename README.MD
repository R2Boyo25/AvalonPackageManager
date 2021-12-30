# Avalon Package Manager

My package manager that installs github repos.
It is meant to be used to compile and install compiled programs but it works with interpreted languages too.

# [Packages repo](https://github.com/R2Boyo25/AvalonPMPackages)

If you don't own the repo that you want to add a package file to, you can add the package file to the packages repo.

# Installation
```bash
git clone https://github.com/R2Boyo25/AvalonPackageManager
cd AvalonPackageManager
python3 install.py
cd ..
rm -rf AvalonPackageManager
```

# Usage
```bash
apm install user/repo
# for my PowderSim repo
apm install r2boyo25/powdersim
# to install a local repo, just use
apm install /path/to/repo
# or
apm install . 
# if you are in the repo's folder
```