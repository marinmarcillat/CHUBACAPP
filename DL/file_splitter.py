# split data into training and testing set
import os, random, shutil, glob2

path_img = r'Q:\test_image_deep_learning\images'

path_train_img = r'Q:\test_image_deep_learning\train_img'
path_train_xml = r'Q:\test_image_deep_learning\train_xml'
path_test_img = r'Q:\test_image_deep_learning\test_img'
path_test_xml = r'Q:\test_image_deep_learning\test_xml'

os.mkdir(path_train_img)
os.mkdir(path_train_xml)
os.mkdir(path_test_img)
os.mkdir(path_test_xml)

image_paths = glob2.glob(os.path.join(path_img,'*.jpg'))
random.shuffle(image_paths)

for i, image_path in enumerate(image_paths):
  if i < int(len(image_paths) * 0.8):
    shutil.copy(os.path.join(path_img,image_path), path_train_img)
    shutil.copy(os.path.join(path_img,image_path.replace(".jpg", ".xml")), path_train_xml)
  else:
    shutil.copy(os.path.join(path_img,image_path), path_test_img)
    shutil.copy(os.path.join(path_img,image_path.replace(".jpg", ".xml")), path_test_xml)