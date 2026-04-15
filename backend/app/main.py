from flask import Flask, render_template, request
import pandas as pd
import joblib

app = Flask(__name__)

bundle = joblib.load("backend/model/fraud_pipeline.joblib")
pipeline = bundle["pipeline"]

@app.route("/", methods=['GET', 'POST'])
def show_input():
    if request.method == 'POST':

        data = {
            "step": int(request.form["step"]),
            "type": request.form["type"],
            "amount": float(request.form["amount"]),
            "oldbalanceOrg": float(request.form["oldBalanceOrig"]),
            "newbalanceOrig": float(request.form["newBalanceOrig"]),
            "oldbalanceDest": float(request.form["oldBalanceDest"]),
            "newbalanceDest": float(request.form["newBalanceDest"]) 
        }

        df = pd.DataFrame([data])

        probability = pipeline.predict_proba(df)[0][1]



        return f"Fraud probability: {probability * 100:.2f}%"

    return render_template("home.html")
if __name__ == '__main__':
    app.run(debug=True)