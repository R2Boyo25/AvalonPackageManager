import sys
#import GUI
import CLI

if len(sys.argv) > 1:
    if sys.argv[1] == '--gui' or sys.argv[1] == '-g':
        try:
            import PyQt5
        except:
            print('PyQt5 not installed')
            quit()
        import GUI
        GUI.main()
    else:
        CLI.main(sys.argv[1:])
else:
    CLI.main(sys.argv[1:])