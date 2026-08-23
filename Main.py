from flask import Flask, render_template, flash, request, session, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import mysql.connector
import matplotlib
import smtplib
import pickle

import numpy as np
import joblib
from tensorflow.keras.models import load_model
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix


app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'


# ✅ FIXED MySQL Connection Function (Bad Handshake Solution)
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",       # ✅ FIX: use 127.0.0.1 instead of localhost
        user="root",
        password="",
        database="1heartdb"     # ✅ FIX: disable ssl handshake issue
    )


# ✅ Load model and preprocessing tools
model = load_model("lstm_attack_model.h5")
scaler = joblib.load("scaler.pkl")
label_encoder = joblib.load("label_encoder.pkl")
features = joblib.load("features.pkl")

# ✅ Load dataset
df = pd.read_csv("UNSW_NB15_train_set.csv")
df.fillna(0, inplace=True)
df = pd.get_dummies(df, columns=['proto', 'service', 'state'])
df['row_id'] = df.index


@app.route("/")
def homepage():
    return render_template('index.html')


@app.route("/Home")
def Home():
    return render_template('index.html')


@app.route("/AdminLogin")
def AdminLogin():
    return render_template('AdminLogin.html')


@app.route("/NewUser")
def NewUser():
    return render_template('NewUser.html')


@app.route("/UserLogin")
def UserLogin():
    return render_template('UserLogin.html')


@app.route("/UserHome")
def UserHome():
    return render_template('UserHome.html')


@app.route("/AdminHome")
def AdminHome():
    return render_template('AdminHome.html')


# -------------------------------
# ✅ PREDICTION PAGE
# -------------------------------
@app.route("/NewQuery1")
def NewQuery1():
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
        return render_template(
            'index1.html',
            features=features,
            ids=available_ids,
            prediction_text=f"Predicted Attack Category: {predicted_class[0]}",
            filled_data=filled_data
        )

    except Exception as e:
        return f"Error: {e}"


@app.route("/UploadDataset")
def UploadDataset():
    return render_template('ViewExcel.html')


# -------------------------------
# ✅ ADMIN LOGIN (FIXED)
# -------------------------------
@app.route("/adminlogin", methods=['GET', 'POST'])
def adminlogin():
    error = None
    if request.method == 'POST':
        uname = request.form['uname']
        password = request.form['password']

        # ✅ FIX: Must be AND (both username & password should match)
        if uname == 'admin' and password == 'admin':
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM register")
                data = cur.fetchall()
                conn.close()
                return render_template('AdminHome.html', data=data)

            except Exception as e:
                return f"MySQL Error: {e}"

        else:
            return render_template('index.html', error=error)

    return render_template("AdminLogin.html")


# -------------------------------
# ✅ USER REGISTER
# -------------------------------
@app.route("/reg", methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        n = request.form['name']
        address = request.form['address']
        age = request.form['age']
        pnumber = request.form['phone']
        email = request.form['email']
        zipc = request.form['zip']
        uname = request.form['uname']
        password = request.form['psw']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO register VALUES ('',%s,%s,%s,%s,%s,%s,%s,%s)",
                (n, age, email, pnumber, zipc, address, uname, password)
            )

            conn.commit()
            conn.close()
            return render_template('UserLogin.html')

        except Exception as e:
            return f"MySQL Error: {e}"

    return render_template("NewUser.html")


# -------------------------------
# ✅ USER LOGIN
# -------------------------------
@app.route("/userlogin", methods=['GET', 'POST'])
def userlogin():
    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['password']
        session['uname'] = username

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM register WHERE uname=%s AND psw=%s", (username, password))
            data = cursor.fetchone()
            conn.close()

            if data is None:
                return render_template('index.html')
            else:
                session['uid'] = data[0]

                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM register WHERE uname=%s AND psw=%s", (username, password))
                user_data = cur.fetchall()
                conn.close()

                return render_template('UserHome.html', data=user_data)

        except Exception as e:
            return f"MySQL Error: {e}"

    return render_template("UserLogin.html")


# -------------------------------
# ✅ USER QUERY + ANSWER
# -------------------------------
@app.route("/UQueryandAns")
def UQueryandAns():
    uname = session.get('uname')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Querytb1 WHERE UserName=%s AND DResult='waiting'", (uname,))
        data = cur.fetchall()

        cur.execute("SELECT * FROM Querytb1 WHERE UserName=%s AND DResult!='waiting'", (uname,))
        data1 = cur.fetchall()

        conn.close()
        return render_template('UserQueryInfo.html', wait=data, answ=data1)

    except Exception as e:
        return f"MySQL Error: {e}"


@app.route("/AdminQinfo")
def AdminQinfo():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Querytb1")
        data = cur.fetchall()
        conn.close()
        return render_template('AdminAnswer.html', data=data)

    except Exception as e:
        return f"MySQL Error: {e}"


@app.route("/AdminAinfo")
def AdminAinfo():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Querytb1 WHERE DResult != 'waiting'")
        data = cur.fetchall()
        conn.close()
        return render_template('AdminAnswer.html', data=data)

    except Exception as e:
        return f"MySQL Error: {e}"


# -------------------------------
# ✅ EXCEL/CSV UPLOAD
# -------------------------------
@app.route("/excelpost", methods=['GET', 'POST'])
def uploadassign():
    if request.method == 'POST':

        file = request.files['fileupload']
        file_extension = file.filename.split('.')[-1]

        import matplotlib.pyplot as plt
        df1 = ''

        if file_extension == 'xlsx':
            df1 = pd.read_excel(file.read(), engine='openpyxl')
        elif file_extension == 'xls':
            df1 = pd.read_excel(file.read())
        elif file_extension == 'csv':
            df1 = pd.read_csv(file)

        import seaborn as sns
        sns.countplot(df1['label'], label="Count")
        plt.savefig('static/images/out.jpg')
        iimg = 'static/images/out.jpg'
        plt.close()

        import model
        return render_template('ViewExcel.html', data=df1.to_html(), dataimg=iimg)

    return render_template("ViewExcel.html")


# -------------------------------
# ✅ RUN APP
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
