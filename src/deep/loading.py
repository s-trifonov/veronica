from model.patch_cropper import PatchCropper
#=================================
def preparePatchTrainData(fullImage, patch_descr):
    cropper = PatchCropper(patch_descr["loc-center"], patch_descr["loc-angle"])
    return cropper.makeArray(fullImage)

#=================================
def preparePackTrainData(fullImage, pack_descr):
    return [(patch_descr, preparePatchTrainData(fullImage, patch_descr))
        for patch_descr in pack_descr["patches"]]
