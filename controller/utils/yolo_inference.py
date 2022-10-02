# -*- coding: utf-8 -*-
"""
@Time ： 2022/10/1 16:37
@Auth ： zxc (https://github.com/linklist2)
@File ：yolo_inference.py
@IDE ：PyCharm
@Function ：yolov5 dnn inference
"""

import cv2
import numpy as np


def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), scaleup=True):
    # Resize and pad image while meeting stride-multiple constraints
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    # Compute padding
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return im


def xywh2xywh(x):
    # Convert nx4 boxes from [x_center, y_center, w, h] to [x_top_left, y_top_left, w, h] where xy1=top-left, xy2=bottom-right
    y = np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    return y


def scale_boxes(img1_shape, boxes, img0_shape):
    # Rescale boxes (xywh) from img1_shape to img0_shape
    # calculate from img0_shape
    gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain  = old / new
    pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding

    boxes[:, 0] -= pad[0]
    boxes[:, 1] -= pad[1]
    boxes[:, :4] /= gain
    clip_boxes(boxes, img0_shape)
    return boxes


def clip_boxes(boxes, shape):
    """超出边界的需要进行clip，并且将（左上角x，左上角y，宽度，高度）->（左上角x，左上角y，右下角x，右下角y）"""
    top_left_x = boxes[:, 0].clip(0, shape[1])
    top_left_y = boxes[:, 1].clip(0, shape[0])
    bottom_right_x = (boxes[:, 0] + boxes[:, 2]).clip(0, shape[1])
    bottom_right_y = (boxes[:, 1] + boxes[:, 3]).clip(0, shape[0])

    boxes[:, 0] = top_left_x
    boxes[:, 1] = top_left_y
    boxes[:, 2] = bottom_right_x
    boxes[:, 3] = bottom_right_y


# 提供20种不同的颜色
colors = [(56, 56, 255), (151, 157, 255), (31, 112, 255), (29, 178, 255), (49, 210, 207), (10, 249, 72), (23, 204, 146),
          (134, 219, 61), (52, 147, 26), (187, 212, 0), (168, 153, 44), (255, 194, 0), (147, 69, 52), (255, 115, 100),
          (236, 24, 0), (255, 56, 132), (133, 0, 82), (255, 56, 203), (200, 149, 255), (199, 55, 255)]


def inference(img_0, target_shape=(640, 640)):
    labels = ['face', 'face_mask']
    resize_shape = target_shape
    img_data = letterbox(img_0, resize_shape)
    # 传入的是BGR，因此使用swapRB得到RGB图像
    img_trans = cv2.dnn.blobFromImage(image=img_data, scalefactor=1 / 255., swapRB=True)
    net = cv2.dnn.readNetFromONNX('models/yolov5n_mask.onnx')
    net.setInput(img_trans)

    # 输入数据，并获得输出，yolov5中将三个检测头的输出合并到了一起
    outputs = net.forward()

    # 进行NMS
    conf_thres = 0.25
    iou_thres = 0.45
    max_wh = 4096

    item = outputs[0]
    # 首先过滤掉obj_conf小于等于阈值的box
    detects = item[item[..., 4] > conf_thres]
    # 将（中心点x,中心点y，宽度，高度）转成cv2.dnn.NMSBoxes所需要的（左上角x，左上角y，宽度，高度）
    detects = xywh2xywh(detects)
    boxes = detects[:, :4]
    # 将后面的分类概率都乘上obj_conf
    detects[:, 5:] *= detects[:, 4:5]
    # 得到每个目标框的最大分类概率,以及其对应的分类序号
    cls_id = np.argmax(detects[:, 5:], axis=1).reshape(-1, 1)
    # 下面这句话效果等同于conf = np.max(detects[:, 5:], axis=1, keepdims=True)，
    # 但是是直接利用argmax得到的结果避免再次排序
    conf = np.take_along_axis(detects[:, 5:], cls_id, axis=1)

    x = np.concatenate((boxes, conf, cls_id), 1)
    # x = x[x[:, 4].argsort()][::-1]

    # (x_center,y_center, width, height)， 所以对box只需要对x_center和y_center加上偏移即可
    # 对每个box+（对应分类序号×一个较大的常数），那么不同分类的box就会因为加的数不同而分离，就避免了可能不同分类box IOU较高而被删除的问题
    bboxes = x[:, :4].copy()
    bboxes[:, :2] += x[:, 5:6] * max_wh
    idx = cv2.dnn.NMSBoxes(bboxes, x[:, 4], conf_thres, iou_thres)

    pred = x[idx]

    # 将box信息映射到原图像当中,并且从（左上角x，左上角y，宽度，高度）->（左上角x，左上角y，右下角x，右下角y）
    scale_boxes(img1_shape=resize_shape, boxes=pred[:, :4], img0_shape=img_0.shape)

    # 在原图像中绘制矩形框
    for box in pred:
        color = colors[int(box[-1]) % len(colors)]
        line_width = max(round(sum(img_0.shape) / 2 * 0.003), 2)  # line width
        # 绘制矩形框
        p1, p2 = (int(box[0]), int(box[1])), (int(box[2]), int(box[3]))
        cv2.rectangle(img_0, p1, p2, color, thickness=line_width, lineType=cv2.LINE_AA)
        # 在矩形框附近添加文字 类别：置信度
        label_text = labels[int(box[-1])] + ' ' + ('%.2f' % box[-2])
        tf = max(line_width - 1, 1)  # font thickness
        w, h = cv2.getTextSize(label_text, 0, fontScale=line_width / 3, thickness=tf)[0]  # text width, height
        outside = p1[1] - h >= 3
        p2 = p1[0] + w, p1[1] - h - 3 if outside else p1[1] + h + 3
        cv2.rectangle(img_0, p1, p2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img_0,
                    label_text, (p1[0], p1[1] - 2 if outside else p1[1] + h + 2),
                    0,
                    line_width / 3,
                    (255, 255, 255),
                    thickness=tf,
                    lineType=cv2.LINE_AA)

    return img_0
