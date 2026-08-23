from flask import Flask, render_template, request
import numpy as np
import joblib
from tensorflow.keras.models import load_model

app = Flask(__name__)

# Load model and preprocessing tools
model = load_model("lstm_attack_model.h5")
scaler = joblib.load("scaler.pkl")
label_encoder = joblib.load("label_encoder.pkl")
features = joblib.load("features.pkl")

@app.route('/')
def index():
    return render_template('index2.html', features=features)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        user_input = [float(request.form.get(col, 0)) for col in features]
        X_scaled = scaler.transform([user_input])
        X_reshaped = X_scaled.reshape(1, len(features), 1)
        prediction = model.predict(X_reshaped)
        predicted_class = label_encoder.inverse_transform([np.argmax(prediction)])
        return render_template('index2.html', features=features, prediction_text=f"Predicted Attack Category: {predicted_class[0]}")
    except Exception as e:
        return render_template('index2.html', features=features, prediction_text=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
