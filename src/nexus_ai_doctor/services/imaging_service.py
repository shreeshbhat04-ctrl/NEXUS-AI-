import os
import logging
import numpy as np
import SimpleITK as sitk

logger = logging.getLogger(__name__)

class ImagingService:
    def reconstruct_ct(self, ap_xray_bytes: bytes, lat_xray_bytes: bytes, output_dir: str) -> str:
        """
        Runs the 3D reconstruction pipeline.
        In this mock/scaffold, it generates a dummy voxel array mimicking a CT scan
        and converts it to a series of 2D DICOM slices.
        """
        logger.info("Running 3D reconstruction pipeline...")
        
        # MOCK INFERENCE: Generate a dummy 128x128x64 3D voxel array
        dummy_voxel_array = np.random.randint(0, 255, size=(64, 128, 128), dtype=np.uint8)
        
        os.makedirs(output_dir, exist_ok=True)
        self.numpy_to_dicom(dummy_voxel_array, output_dir)
        
        return output_dir

    def numpy_to_dicom(self, voxel_array: np.ndarray, output_dir: str):
        # sitk expects array in (z, y, x) format
        image = sitk.GetImageFromArray(voxel_array)
        
        # Set basic DICOM metadata (spacing, origin)
        image.SetSpacing([1.0, 1.0, 1.0]) 
        
        # Write the 3D volume as a series of 2D DICOM slices
        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()
        
        for i in range(image.GetDepth()):
            slice_image = image[:, :, i]
            writer.SetFileName(os.path.join(output_dir, f"slice_{i:03d}.dcm"))
            writer.Execute(slice_image)
            
        logger.info(f"Saved {image.GetDepth()} DICOM slices to {output_dir}")
