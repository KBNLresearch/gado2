#!/usr/bin/env python3

import torch

if torch.cuda.is_available():
    device = torch.device('cuda')
    print('CUDA device:', device)
    print(torch.cuda.get_device_name(0))
    print('mem allocated:', round(torch.cuda.memory_allocated(0)/1024**3,1), 'GB')
    print('mem reserved:' , round(torch.cuda.memory_reserved(0)/1024**3,1), 'GB')
else:
    print("No CUDA support")
