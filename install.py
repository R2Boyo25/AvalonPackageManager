import os

print("Install dependencies.....")
os.system("pip3 install -r requirements.txt")

print("Installing APM using APM...")
os.system("python3 ./main.py install R2Boyo25/AvalonPackageManager")

print("Done.")
print("It is now safe to delete the AvalonPackageManager folder you have just downloaded, as it has been downloaded and installed to Avalon's directory.")