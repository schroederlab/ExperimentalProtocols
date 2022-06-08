# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 17:05:10 2022

@author: maria
"""


import time, os
import numpy as np
from suite2p.registration import register, rigid
from suite2p.io import tiff_to_binary, BinaryRWFile
from suite2p import io
from suite2p import default_ops
from tifffile import imread
import matplotlib.pyplot as plt

### RUN options
# main ops
ops = default_ops()
ops['data_path'] = ['D:/DATA/M170821_SS075_2017-09-13/2/']
ops['look_one_level_down'] = True
ops['ignore_flyback'] = [0,1,2]
ops['nchannels'] = 2
ops['nplanes'] = 8
ops['functional_chan'] = 1

# registration ops
ops['keep_movie_raw'] = True
ops['align_by_chan'] = 2

# run for only X number frames
#ops['frames_include'] = 1000    

### convert tiffs to binaries

# set save folder
ops['save_path0'] = ops['data_path'][0]
if 'save_folder' not in ops or len(ops['save_folder'])==0:
    ops['save_folder'] = 'suite2p'
save_folder = os.path.join(ops['save_path0'], ops['save_folder'])
os.makedirs(save_folder, exist_ok=True)

#ops = tiff_to_binary(ops)

from natsort import natsorted
plane_folders = natsorted([ f.path for f in os.scandir(save_folder) if f.is_dir() and f.name[:5]=='plane'])
ops_paths = [os.path.join(f, 'ops.npy') for f in plane_folders]
nplanes = len(ops_paths)

### compute reference images

refImgs = []

for ipl, ops_path in enumerate(ops_paths):
    if ipl in ops['ignore_flyback']:
        print('>>>> skipping flyback PLANE', ipl)
        continue
    
    ops = np.load(ops_path, allow_pickle=True).item()
    align_by_chan2 = ops['functional_chan'] != ops['align_by_chan']
    raw = ops['keep_movie_raw']
    reg_file = ops['reg_file']
    raw_file = ops.get('raw_file', 0) if raw else reg_file
    if ops['nchannels'] > 1:
        reg_file_chan2 = ops['reg_file_chan2']
        raw_file_chan2 = ops.get('raw_file_chan2', 0) if raw else reg_file_chan2
    else:
        reg_file_chan2 = reg_file 
        raw_file_chan2 = reg_file 
    
    align_file = reg_file_chan2 if align_by_chan2 else reg_file
    align_file_raw = raw_file_chan2 if align_by_chan2 else raw_file
    Ly, Lx = ops['Ly'], ops['Lx']
    
    ### compute reference image
    
    # grab frames
    with BinaryRWFile(Ly=Ly, Lx=Lx, filename=align_file_raw) as f_align_in:
        n_frames = f_align_in.shape[0]
        frames = f_align_in[np.linspace(0, n_frames, 1 + np.minimum(ops['nimg_init'], n_frames), dtype=int)[:-1]]    
    
    # compute bidiphase shift
    if ops['do_bidiphase'] and ops['bidiphase'] == 0 and not ops['bidi_corrected']:
        bidiphase = bidiphase.compute(frames)
        print('NOTE: estimated bidiphase offset from data: %d pixels' % bidiphase)
        ops['bidiphase'] = bidiphase
        # shift frames
        if bidiphase != 0:
            bidiphase.shift(frames, int(ops['bidiphase']))
    else:
        bidiphase = 0
        
    # compute reference image
    refImgs.append(register.compute_reference(frames))


### align reference frames to each other

frames = np.array(refImgs).copy()
for frame in frames:
    rmin, rmax = np.int16(np.percentile(frame,1)), np.int16(np.percentile(frame,99))
    frame[:] = np.clip(frame, rmin, rmax)
    
refImg = frames.mean(axis=0)

niter = 8
for iter in range(0, niter):
    # rigid registration
    ymax, xmax, cmax = rigid.phasecorr(
        data=rigid.apply_masks(frames, *rigid.compute_masks(refImg=refImg,
                                                            maskSlope=ops['spatial_taper'] if ops['1Preg'] else 3 * ops['smooth_sigma'])),
        cfRefImg=rigid.phasecorr_reference(refImg=refImg, smooth_sigma=ops['smooth_sigma']),
        maxregshift=ops['maxregshift'],
        smooth_sigma_time=ops['smooth_sigma_time'],
    )
    dys = np.zeros(len(frames), 'int')
    dxs = np.zeros(len(frames), 'int')
    for i, (frame, dy, dx) in enumerate(zip(frames, ymax, xmax)):
        frame[:] = rigid.shift_frame(frame=frame, dy=dy, dx=dx)
        dys[i] = dy
        dxs[i] = dx
        
print('shifts of reference images: (y,x) = ', dys, dxs)

refImgs = list(frames)


import imp
from suite2p.registration import utils, rigid
imp.reload(utils)
imp.reload(rigid)
imp.reload(register)

from os import path
for ipl, ops_path in enumerate(ops_paths):
    if ipl in ops['ignore_flyback']:
        print('>>>> skipping flyback PLANE', ipl)
        continue
    else:
        print('>>>> registering PLANE', ipl)
    ops = np.load(ops_path, allow_pickle=True).item()
    ops = register.register_binary(ops, refImg=refImgs)
    np.save(ops['ops_path'], ops)

ops['yoff']

for ipl, ops_path in enumerate(ops_paths):
    if ipl in ops['ignore_flyback']:
        print('>>>> skipping flyback PLANE', ipl)
        continue
    
    ops = np.load(ops_path, allow_pickle=True).item()
    plt.plot(ops['zpos_registration'][:500])