from PIL import Image
import jax.numpy as jnp

from model.cropper import Cropper
#=================================
def _prepareCroppedImage(fullImage, cropper):
    p_poly = cropper.getPoly(False)
    x1 = min(pp[0] for pp in p_poly)
    x2 = max(pp[0] for pp in p_poly)
    y1 = min(pp[1] for pp in p_poly)
    y2 = max(pp[1] for pp in p_poly)
    if cropper.getAngle() == 0:
        return fullImage.crop([x1, y1, x2, y2])
    local_image = fullImage.crop([
        x1 - 1, y1 - 1, x2 + 1 , y2 + 1])
    rotated_image = local_image.rotate(cropper.getAngle(),
        resample=Image.Resampling.BILINEAR)
    rx = round((rotated_image.height - cropper.getSize())/2)
    ry = round((rotated_image.width - cropper.getSize())/2)
    return rotated_image.crop([rx, ry,
        rx + cropper.getSize(), ry + cropper.getSize()])

#=================================
def preparePatchData(fullImage, cropper, save_file = None):
    image = _prepareCroppedImage(fullImage, cropper)
    img_input = jnp.asarray(image)
    if save_file is not None:
        image.save(save_file)
    assert img_input.shape == (128, 128)
    if len(img_input.shape) != 2:
        assert len(img_input.shape) == 3
        img_input = jnp.average(img_input, 2)
    return img_input

#=================================
#_DEBUG_COUNT = 10
def preparePatchTrainData(fullImage, patch_descr):
    #global _DEBUG_COUNT
    cropper = Cropper(patch_descr["loc-center"], patch_descr["loc-angle"])
    save_file = None
    #if patch_descr["target"][-1] in (1, 2):
    #    _DEBUG_COUNT -= 1
    #    if _DEBUG_COUNT == 0:
    #        save_file = "_here.tif"
    #        print("Patch:", json.dumps(patch_descr))
    return (preparePatchData(fullImage, cropper, save_file),
        jnp.array(patch_descr["target"]))

#=================================
def preparePackTrainData(fullImage, pack_descr):
    return [preparePatchTrainData(fullImage, patch_descr)
        for patch_descr in pack_descr["patches"]]


