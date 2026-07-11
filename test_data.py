import os

folders = ['data/dfsar', 'data/ohrc', 'data/dem']

for folder in folders:
    print('\n=== ' + folder + ' ===')
    if os.path.exists(folder):
        files = os.listdir(folder)
        if files:
            for f in files:
                full = folder + '/' + f
                size = os.path.getsize(full)
                print('  ' + f + ' --- ' + str(round(size/1e6, 1)) + ' MB')
        else:
            print('  Empty!')
    else:
        print('  Folder not found!')