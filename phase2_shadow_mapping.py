import numpy as np
import matplotlib.pyplot as plt
import struct
import os

print("=== Phase 2: Shadow Region Mapping ===")

# Read the label file first to get image dimensions
lbr_file = 'data/ohrc/data/calibrated/20260103/ch2_ohr_ncp_20260103T1005176450_d_img_d18.lbr'
img_file = 'data/ohrc/data/calibrated/20260103/ch2_ohr_ncp_20260103T1005176450_d_img_d18.img'

# Read label to get dimensions
rows, cols = None, None
with open(lbr_file, 'r') as f:
    for line in f:
        if 'LINES' in line and '=' in line:
            try:
                rows = int(line.split('=')[1].strip())
                print('Rows:', rows)
            except:
                pass
        if 'LINE_SAMPLES' in line and '=' in line:
            try:
                cols = int(line.split('=')[1].strip())
                print('Cols:', cols)
            except:
                pass

print('Image dimensions:', rows, 'x', cols)

# Read raw image data
if rows and cols:
    data = np.fromfile(img_file, dtype=np.uint16)
    print('Total pixels read:', len(data))
    
    # Take small patch for testing
    patch = data[:2000*2000].reshape(2000, 2000)
    
    print('Min:', patch.min())
    print('Max:', patch.max())
    print('Mean:', round(patch.mean(), 2))
    
    plt.figure(figsize=(10, 8))
    plt.imshow(patch, cmap='gray')
    plt.colorbar(label='Brightness')
    plt.title('OHRC Image Patch - Lunar South Polar Region')
    plt.savefig('outputs/ohrc_patch.png', dpi=150)
    plt.show()
    print('Saved to outputs/ohrc_patch.png')