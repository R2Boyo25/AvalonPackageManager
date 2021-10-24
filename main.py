import sys
import CLI

if len(sys.argv) > 0:
    CLI.main(sys.argv[1:])
else:
    print("Please provide at least one argument!")