from flask import Flask, render_template, request, send_file
import numpy as np
import joblib
from tensorflow.keras.models import load_model
import pandas as pd

app = Flask(__name__)

# Load model and preprocessing tools
model = load_model("lstm_attack_model.h5")
scaler = joblib.load("scaler.pkl")
label_encoder = joblib.load("label_encoder.pkl")
features = joblib.load("features.pkl")

# Load the dataset
df = pd.read_csv("UNSW_NB15_train_set.csv")
df.fillna(0, inplace=True)
df = pd.get_dummies(df, columns=['proto', 'service', 'state'])
df['row_id'] = df.index

@app.route('/')
def index():
    available_ids = df['row_id'].tolist()[:100]
    filled_data = {col: 0 for col in features}
    return render_template('index1.html', features=features, ids=available_ids, filled_data=filled_data)

@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    row_id = int(request.form['selected_id'])
    row = df[df['row_id'] == row_id]
    filled_data = {col: row.iloc[0].get(col, 0) for col in features}
    available_ids = df['row_id'].tolist()[:100]
    return render_template('index1.html', features=features, ids=available_ids, filled_data=filled_data, selected_id=row_id)

@app.route('/download_csv', methods=['POST'])
def download_csv():
    row_id = int(request.form['selected_id'])
    row = df[df['row_id'] == row_id][features]
    file_path = "selected_row.csv"
    row.to_csv(file_path, index=False)
    return send_file(file_path, as_attachment=True)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        input_data = [float(request.form.get(col, 0)) for col in features]
        filled_data = {col: request.form.get(col, 0) for col in features}
        X_scaled = scaler.transform([input_data]).reshape(1, len(features), 1)
        prediction = model.predict(X_scaled)
        predicted_class = label_encoder.inverse_transform([np.argmax(prediction)])
        available_ids = df['row_id'].tolist()[:100]
        return render_template('index1.html', features=features, ids=available_ids,
                               prediction_text=f"Predicted Attack Category: {predicted_class[0]}",
                               filled_data=filled_data)
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True)