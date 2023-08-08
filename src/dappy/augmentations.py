import numpy as np
import pandas as pd
from typing import Union, List, Dict
import numpy as np
import tqdm


def expand_meta(meta: pd.DataFrame, ids: pd.DataFrame, reps: int):
    # Tile pandas DataFrame
    meta_expanded = pd.DataFrame(np.tile(meta.values.T, reps).T, columns=meta.columns)
    meta_expanded["old_id"] = meta_expanded["id"].copy()
    meta_expanded["id"] = meta_expanded.index

    # Repeating ids
    # ids_expanded = np.tile(ids, reps).reshape((reps, -1))
    # ids_expanded += np.arange(reps)[:, None] * (np.max(ids_expanded) + 1)
    ids_expanded = (
        np.add.outer(ids, np.arange(0, reps) * (np.max(ids) + 1))
        .T.flatten()
        .astype(ids.dtype)
    )

    assert (
        np.sum(
            ids_expanded[-len(ids) :]
            - ids_expanded[: len(ids)]
            - (np.max(ids) + 1) * (reps - 1)
        )
        == 0
    )
    assert np.sum(ids_expanded[: len(ids)] - ids) == 0

    return meta_expanded, ids_expanded


def joint_ablation(
    pose: np.ndarray,
    joint_groups: Dict,
    ablations: List,
    ids: Union[np.ndarray, List],
    meta: pd.DataFrame,
):
    # Pose is forward facing and centered
    if any([" " in key for key in joint_groups.keys()]):
        raise Exception("Cannot be spaces in joint_groups keys")

    pose_means = pose.mean(axis=0)
    label = ["Normal"] * len(meta)
    pose_augmented = [pose]
    ## Ablations
    for i, keys in enumerate(tqdm.tqdm(ablations)):
        if " " in keys:  # For multi-group ablation
            keypt_indices = []
            for key in keys.split(" "):
                keypt_indices += joint_groups[key]
        else:
            keypt_indices = joint_groups[keys]
        pose_temp = pose.copy()
        # Impute with the mean
        pose_temp[:, keypt_indices, :] = pose_means[None, keypt_indices, :]
        pose_augmented += [pose_temp]

        ## Adjust metadata
        label += [keys] * len(meta)

    pose_augmented = np.concatenate(pose_augmented, axis=0)

    num_augs = len(ablations) + 1
    meta_expanded, ids_expanded = expand_meta(meta, ids, num_augs)
    meta_expanded["joint_ablation"] = label

    return pose_augmented, meta_expanded, ids_expanded


def mirror(
    pose: np.ndarray,
    joint_pairs: np.ndarray,
    ids: Union[np.ndarray, List],
    meta: pd.DataFrame,
):
    # Pose is forward facing and centered
    pose_flip = pose.copy()
    pose_flip[..., 1] = -pose_flip[..., 1]  # Flip Y
    joint_temp = pose_flip[:, joint_pairs[:, 0], :]
    pose_flip[:, joint_pairs[:, 0], :] = pose_flip[
        :, joint_pairs[:, 1], :
    ]  # Flip joint pairs
    pose_flip[:, joint_pairs[:, 1], :] = joint_temp
    pose_augmented = np.concatenate([pose, pose_flip], axis=0)

    meta_expanded, ids_expanded = expand_meta(meta, ids, 2)
    label = ["Original"] * len(meta) + ["Mirrored"] * len(meta)
    meta_expanded["mirror"] = label

    return pose_augmented, meta_expanded, ids_expanded


def noise(
    pose: np.ndarray,
    level: Union[np.ndarray, List],
    ids: Union[np.ndarray, List],
    meta: pd.DataFrame,
):
    # Assumes first element of "level" is 0
    noise = np.zeros(np.shape(pose), dtype=pose.dtype)
    for lev in level[1:]:
        rng = np.random.default_rng()
        noise = np.append(
            noise, np.random.normal(0, lev, np.shape(pose)), axis=0
        ).astype(pose.dtype)

    pose_augmented = np.tile(pose.T, len(level)).T
    assert np.sum(pose_augmented[:len(pose)] - pose) == 0
    pose_augmented += noise
    meta_expanded, ids_expanded = expand_meta(meta, ids, len(level))
    meta_expanded['noise'] = np.repeat(level,np.max(ids)+1)

    return pose_augmented, meta_expanded, ids_expanded
