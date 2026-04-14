from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def show_input():
    if request.method == 'POST':

        step = request.form["step"]
        type = request.form["type"]
        amount = request.form["amount"]
        oldbalanceOrg = request.form["oldBalanceOrig"]
        newbalanceOrig = request.form["newBalanceOrig"]
        oldbalanceDest = request.form["oldBalanceDest"]
        newbalanceDest = request.form["newBalanceDest"]

        return f"{step}, {type}, {amount}, {oldbalanceOrg}, {newbalanceOrig}, {oldbalanceDest}, {newbalanceDest}"

    return render_template("home.html")
if __name__ == '__main__':
    app.run(debug=True)