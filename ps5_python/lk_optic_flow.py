import cv2
import numpy as np
from grad_utils import *

def lk_optic_flow(frame1, frame2, win=2):
    '''
    The code below was borrowed from stackoverflow
    ../questions/14321092/lucas-kanade-python-numpy-implementation-uses-enormous-amount-of-memory
    '''

    # calculate gradients in x, y and t dimensions
    Ix = np.zeros(frame1.shape, dtype=np.float32)
    Iy = np.zeros(frame1.shape, dtype=np.float32)
    It = np.zeros(frame1.shape, dtype=np.float32)
    Ix[1:-1, 1:-1] = (frame1[1:-1, 2:] - frame1[1:-1, :-2]) / 2
    Iy[1:-1, 1:-1] = (frame1[2:, 1:-1] - frame1[:-2, 1:-1]) / 2
    It[1:-1, 1:-1] = frame1[1:-1, 1:-1] - frame2[1:-1, 1:-1]

    params = np.zeros(frame1.shape + (5,))
    params[..., 0] = Ix ** 2
    params[..., 1] = Iy ** 2
    params[..., 2] = Ix * Iy
    params[..., 3] = Ix * It
    params[..., 4] = Iy * It
    del It, Ix, Iy
    cum_params = np.cumsum(np.cumsum(params, axis=0), axis=1)
    del params
    win_params = (cum_params[2 * win + 1:, 2 * win + 1:] -
                  cum_params[2 * win + 1:, :-1 - 2 * win] -
                  cum_params[:-1 - 2 * win, 2 * win + 1:] +
                  cum_params[:-1 - 2 * win, :-1 - 2 * win])
    del cum_params
    op_flow = np.zeros(frame1.shape + (2,))
    det = win_params[...,0] * win_params[..., 1] - win_params[..., 2] **2

    op_flow_x = np.where(det != 0,
                         (win_params[..., 1] * win_params[..., 3] -
                          win_params[..., 2] * win_params[..., 4]) / det,
                         0)
    op_flow_y = np.where(det != 0,
                         (win_params[..., 0] * win_params[..., 4] -
                          win_params[..., 2] * win_params[..., 3]) / det,
                         0)
    op_flow[win + 1: -1 - win, win + 1: -1 - win, 0] = op_flow_x[:-1, :-1]
    op_flow[win + 1: -1 - win, win + 1: -1 - win, 1] = op_flow_y[:-1, :-1]
    op_flow = op_flow.astype(np.float32)
    return op_flow

def my_lk_optic_flow(frame1, frame2, filter_size=5, threshold=0):
    '''
    My lucas kanade optic flow implementation
    '''
    It = cv2.GaussianBlur(frame2 - frame1, (5,5), 0)
    Ix = cv2.GaussianBlur(cv2.Sobel(frame1, cv2.CV_64F, 1, 0, 5), (5,5), 0)
    Iy = cv2.GaussianBlur(cv2.Sobel(frame1, cv2.CV_64F, 0, 1, 5), (5,5), 0)
    Ixx = Ix * Ix
    Iyy = Iy * Iy
    Ixy = Ix * Iy
    Ixt = Ix * It
    Iyt = Iy * It

    # calculate the gradient product accumulations for each pixel
    Sxx = cv2.boxFilter(Ixx, -1, ksize=(filter_size,)*2, normalize=True)
    Sxy = cv2.boxFilter(Ixy, -1, ksize=(filter_size,)*2, normalize=True)
    Syy = cv2.boxFilter(Iyy, -1, ksize=(filter_size,)*2, normalize=True)
    Sxt = cv2.boxFilter(Ixt, -1, ksize=(filter_size,)*2, normalize=True)
    Syt = cv2.boxFilter(Iyt, -1, ksize=(filter_size,)*2, normalize=True)
    del It, Ix, Iy, Ixx, Ixy, Iyy, Ixt, Iyt
    # calculate the displacement matrices U, V
    rows, cols = frame1.shape
    flow = np.zeros((rows, cols, 2), dtype=np.float64)
    A = np.dstack((Sxx, Sxy, Sxy, Syy))
    b = np.dstack((-Sxt, -Syt))
    #  threshold = 100
    for r in range(rows):
        for c in range(cols):
            flow[r,c,:] = np.linalg.lstsq(A[r,c].reshape((2,2)), b[r,c])[0]
            #  ev,_ = np.linalg.eig(A[r,c].reshape((2,2)))
            #  if ev[1] >= threshold and ev[0] >= threshold:
                #  flow[r,c,:] = np.dot(np.linalg.inv(A[r,c].reshape((2,2))), b[r,c])
            #  elif ev[1] >= threshold and ev[0] < threshold:
                #  flow[r,c,:] = np.linalg.lstsq(A[r,c].reshape((2,2)), b[r,c])[0]
            #  else:
                #  flow[r,c,:] = 0

    flow = -flow.astype(np.float32)
    return flow
