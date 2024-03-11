import time
import torch
import sys

import os

os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

# 测试gpu计算耗时
A = torch.ones(5000, 5000).to('cuda')
B = torch.ones(5000, 5000).to('cuda')
startTime2 = time.time()
for i in range(100):
    C = torch.matmul(A, B)
endTime2 = time.time()
print('gpu:', round((endTime2 - startTime2) * 1000, 2), 'ms')

sys.exit(1)

# # 测试cpu计算耗时
# A = torch.ones(5000, 5000)
# B = torch.ones(5000, 5000)
# startTime1 = time.time()
# for i in range(100):
#     C = torch.matmul(A, B)
# endTime1 = time.time()
# print('cpu:', round((endTime1 - startTime1) * 1000, 2), 'ms')