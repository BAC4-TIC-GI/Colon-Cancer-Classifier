import joblib
import os, pathlib

model_path = pathlib.Path('cc_model.pkl').resolve().parent.parent
path_to_model = pathlib.Path("cc_model.pkl")

print(model_path, "\n", path_to_model)

try:
    model = joblib.load(model_path)
    print(model)
except Exception as e:
    print("Error: ", str(e))