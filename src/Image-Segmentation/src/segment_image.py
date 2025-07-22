from mmseg.apis import inference_model, init_model, show_result_pyplot
import mmcv
import os
import cv2



def generate_segmentated_img(img_path):
    config_dir = 'config'
    config_path = os.path.join(config_dir, 'deeplabv3plus_r50-d8_4xb2-300k_mapillay_v1_65-1280x1280.py')
    checkpoint_path = os.path.join(config_dir, 'deeplabv3plus_r50-d8_4xb2-300k_mapillay_v1_65-1280x1280_20230301_110504-655f8e43.pth')
    # build the model from a config file and a checkpoint file
    model = init_model(config_path, checkpoint_path, device='cuda:0')

    # test a single image and show the results
    result = inference_model(model, img_path)
    vis_image = show_result_pyplot(model, img_path, result,opacity=1,show=False,with_labels=False)
    #print(vis_image.shape)
    return vis_image

