import pickle


pkl = r"E:\ATI_force\tactile_feature_extraction\saved_data\tip_1\time_series\sample_1.pkl"  # ← 改成你的 .cal
pkl = r"E:\ATI_force\tactile_feature_extraction\saved_data\collect_new_tip5_5D_surface\time_series\sample_5.pkl"  # ← 改成你的 .cal


with open(pkl, "rb") as f:
    data = pickle.load(f)
print(data)
