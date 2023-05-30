from features import *
import DataStruct as ds
import visualization as vis
import interface as itf
import numpy as np
import time
import read, write
from embed import Watershed, Embed
import pickle
import analysis
import run
from pathlib import Path
from tqdm import tqdm

analysis_key = "ensemble_healthy"
paths = read.config("../configs/path_configs/" + analysis_key + ".yaml")
params = read.config("../configs/param_configs/fitsne.yaml")

if Path(paths["out_path"] + params["label"] + "/datastruct.p").exists():
    data_obj = pickle.load(
        open("".join([paths["out_path"], params["label"], "/datastruct.p"]), "rb")
    )

else:
    connectivity = read.connectivity(
        path=paths["skeleton_path"], skeleton_name=paths["skeleton_name"]
    )

    pose, id = read.pose_h5(paths["data_path"] + "pose_aligned.h5")
    pose = pose[::2, ...]
    id = id[::2, ...]

    meta, meta_by_frame = read.meta(paths["meta_path"], id=id)

    pose_rot = rotate_spine(center_spine(pose))
    features, labels = run.standard_features(pose_rot, connectivity, paths)

    
    data_obj = run.run(
        features,
        labels,
        pose,
        id,
        connectivity,
        paths,
        params,
        meta,
        meta_by_frame
    )
    # print("Writing Data Object to pickle")
    data_obj.write_pickle("".join([paths["out_path"], params["label"], "/"]))

kpms_syllables = pickle.load(
        open("".join([paths["out_path"],"/syllables_reindexed.p"]), "rb")
    )

data_obj.data["State"] = np.concatenate(tuple(kpms_syllables.values()))[::params['downsample']]

# for state in range(100):
#     state_bool = data_obj.data["State"].values.astype(int) == state
#     sizes = [20 if is_state else 3 for is_state in state_bool]
#     # import pdb; pdb.set_trace()
#     vis.scatter_by_cat(data_obj.embed_vals, 1*state_bool, color = [(0.5,0.5,0.5), (1, 0.5, 0)], size = sizes,
#                        label='state',filepath = ''.join([paths['out_path'],params['label'],'/state/',str(state),'_']))

# vis.density(
#     data_obj.ws.density,
#     data_obj.ws.borders,
#     filepath="".join([paths["out_path"], params["label"], "/density.png"]),
#     show=False,
# )

# vis.scatter(
#     data_obj.embed_vals,
#     filepath="".join([paths["out_path"], params["label"], "/scatter.png"]),
# )

# for cat in params["density_by_column"]:
#     vis.density_cat(
#         data=data_obj,
#         column=cat,
#         watershed=data_obj.ws,
#         n_col=4,
#         filepath="".join(
#             [paths["out_path"], params["label"], "/density_", cat, ".png"]
#         ),
#     )



vis.skeleton_vid3D_cat(
    data_obj,
    "State",
    n_skeletons=10,
    filepath="".join([paths["out_path"], params["label"], "/state/"]),
)
