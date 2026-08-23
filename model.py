import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical

# Load dataset
df = pd.read_csv("UNSW_NB15_train_set.csv")
df['attack_cat'] = df['attack_cat'].fillna('Normal')

# One-hot encode categorical features
df = pd.get_dummies(df, columns=['proto', 'service', 'state'])

# Encode target labels
le = LabelEncoder()
df['attack_cat_encoded'] = le.fit_transform(df['attack_cat'])
y = to_categorical(df['attack_cat_encoded'])

# Feature selection
X = df.drop(['label', 'attack_cat', 'attack_cat_encoded'], axis=1)
features = X.columns.tolist()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_scaled = X_scaled.reshape(X_scaled.shape[0], X_scaled.shape[1], 1)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# LSTM model
model = Sequential()
model.add(LSTM(64, input_shape=(X_train.shape[1], 1)))
model.add(Dropout(0.3))
model.add(Dense(32, activation='relu'))
model.add(Dense(y.shape[1], activation='softmax'))

model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=10, batch_size=128, validation_data=(X_test, y_test))

# Save model and preprocessors
model.save("lstm_attack_model.h5")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(le, "label_encoder.pkl")
joblib.dump(features, "features.pkl")

print("LSTM model trained and saved.")
