import os
import pandas as pd
import numpy as np

from tactile_feature_extraction import BASE_DATA_PATH

data_path     = BASE_DATA_PATH
indir_name    = "data"
outdir_names  = ["train", "val"]
split         = 0.8           # 训练集占比
need_total    = 1500          # <── 新增：期望总样本数（None 或 <= 实际行数）

# 1. 读标签 -----------------------------------------------------------------
targets_df = pd.read_csv(f"{data_path}/labels.csv")

# 2. 如果需要裁剪总量 --------------------------------------------------------
if need_total is not None and need_total < len(targets_df):
    targets_df = (
        targets_df.sample(n=need_total, random_state=0)  # 可复现随机抽样
                  .reset_index(drop=True)
    )

# 3. 一次性补全绝对路径（循环外） -------------------------------------------
targets_df["image_name"] = (
    f"{data_path}/processed_frames/" + targets_df.image_name.astype(str)
)

# 4. 生成与 targets_df 同长的布尔掩码 ---------------------------------------
np.random.seed(0)
inds_true = np.random.choice(
    [True, False],
    size=len(targets_df),               # 长度 == 当前 DataFrame
    p=[split, 1 - split]
)
inds = [inds_true, ~inds_true]

# 5. 写入 train / val -------------------------------------------------------
for outdir_name, ind in zip(outdir_names, inds):
    outdir = os.path.join(data_path, "linshear_surface_3d", "nanoTip", outdir_name)
    os.makedirs(outdir, exist_ok=True)
    targets_df[ind].to_csv(os.path.join(outdir, "targets.csv"), index=False)


# data_path = BASE_DATA_PATH
# indir_name = "data"
# outdir_names = ["train", "val"]
# split = 0.8

# targets_df = pd.read_csv(f'{data_path}/labels.csv')

# # Select data
# np.random.seed(0) # make predictable
# path=f'{data_path}/raw_frames'
# file_num=[f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f)) ]
# inds_true = np.random.choice([True, False], size=len(file_num), p=[split, 1-split])
# inds = [inds_true, ~inds_true]

# # iterate over split
# for outdir_name, ind in zip(outdir_names, inds):

#     indir = os.path.join(data_path, indir_name)
#     outdir = os.path.join(data_path, 'linshear_surface_3d', 'nanoTip', outdir_name)

#     # point image names to indir
#     targets_df['image_name'] = f'{data_path}/processed_frames/' + targets_df.image_name.map(str) 

#     os.makedirs(outdir, exist_ok=True)

#     # populate outdir
#     targets_df[ind].to_csv(os.path.join(outdir, 'targets.csv'), index=False)
#     targets_df = pd.read_csv(f'{data_path}/labels.csv')