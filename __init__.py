import os

ROOT_PATH = os.path.join(os.path.dirname(__file__), 'saved_data')

# Model Paths
TIP_ID = 'new_tip5'
#TIP_ID = 'MAY30_TIP1'   
#TIP_ID = 'TIP5'   

BASE_DATA_PATH = os.path.join(ROOT_PATH, f"collect_{TIP_ID}_5D_surface")
BASE_MODEL_PATH = os.path.join(ROOT_PATH, f"collect_{TIP_ID}_5D_surface", "model")

SAVED_MODEL_PATH = os.path.join('E:/Data/ftp_agg/models/non_async/linshear_surface_3d/nanoTip/simple_cnn') # For transfer learning
