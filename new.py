import pickle, json

in_path  = "/home/wenhao/tactile_feature_extraction-dev/tactile_feature_extraction/saved_data/collect_TIP5_5D_surface/time_series/sample_6998.pkl"
#in_path = "/home/wenhao/tactile_feature_extraction-dev/tactile_feature_extraction/saved_data/collect_MAY28_tip4_5D_surface/time_series/sample_699.pkl"  # 想读取的 pkl 名
#in_path = "/home/wenhao/tactile_feature_extraction-dev/tactile_feature_extraction/saved_data/collect_MAY22_tip3_5D_surface/backup/time_series/sample_1.pkl"
#in_path = "/home/wenhao/tactile_feature_extraction-dev/tactile_feature_extraction/saved_data/collect_test1_5D_surface/time_series/sample_1.pkl"  # 想读取的 pkl 名
out_path = "output.txt"       # 想保存的 txt 名

with open(in_path, "rb") as f:
    obj = pickle.load(f)

# 方法 A：直接 str()，最简单
with open(out_path, "w", encoding="utf-8") as f:
    f.write(str(obj))

# 方法 B：若对象是 JSON 可序列化的（list / dict / str / int / float / bool / None），推荐：
# txt 里更易读，也便于之后再解析
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(obj, f, ensure_ascii=False, indent=2)
