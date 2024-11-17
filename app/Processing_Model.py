import cv2
import numpy as np
import pytesseract
import os

######  ------>> For Splitting Full Name in 3 Parts (First Name, Last Name, Surname) ######

def split_full_name(full_name):
    name_parts = full_name.split()
    if len(name_parts) >= 3:
        first_name = name_parts[0]
        surname = name_parts[-1]
        last_name = ' '.join(name_parts[1:-1])
        return first_name, last_name, surname
    else:
        return None, None, None

#####  ------>> For Separating Name and Pancard Id   #####

def separate_names_and_ids(mixed_list):
    data = []
    for i in range(0, len(mixed_list), 2):
        full_name = mixed_list[i]
        user_id = mixed_list[i + 1]
        first_name, last_name, surname = split_full_name(full_name)
        if first_name and last_name and surname:
            data.append(first_name)
            data.append(last_name)
            data.append(surname)
            data.append(user_id)
    return data

def process_image(image,img2):
    imgQ = cv2.imread(img2)
    h, w, c = imgQ.shape 
    orb = cv2.ORB_create(10000)

    kp1, des1 = orb.detectAndCompute(imgQ, None)

    per = 25
    roi = [[(68, 294), (502, 338), 'text', 'Full Name'],
           [(238, 194), (552, 276), 'text', 'id']]
    
    ocrData = []

    kp2, des2 = orb.detectAndCompute(image, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = list(bf.match(des2, des1))
    matches.sort(key=lambda x: x.distance)
    good = matches[:int(len(matches) * (per / 100))]
    imgMatch = cv2.drawMatches(image, kp2, imgQ, kp1, good[:90], None, flags=2)

    srcPoints = np.float32([kp2[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    desPoints = np.float32([kp1[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    M, _ = cv2.findHomography(srcPoints, desPoints, cv2.RANSAC, 5)

    imgScan = cv2.warpPerspective(image, M, (w, h))

    imgShow = imgScan.copy()
    imgMask = np.zeros_like(imgShow)

    for x, r in enumerate(roi):
        cv2.rectangle(imgMask, (r[0][0], r[0][1]), (r[1][0], r[1][1]), (0, 255, 0), cv2.FILLED)

        imgCrop = imgScan[r[0][1]:r[1][1], r[0][0]:r[1][0]]
        raw_text = pytesseract.image_to_string(imgCrop)
        ocrData.append(raw_text.strip())

    data = separate_names_and_ids(ocrData)
    return data
## For Just My Testing  Only//

# image = 'pan/Test(2)_16x9.png'
# result = process_image(image)
# print("First Name   -- ",result[0])
# print("Last Name    -- ",result[1])
# print("Surname Name -- ",result[2])
# print("Pancard Id   -- ",result[3])

