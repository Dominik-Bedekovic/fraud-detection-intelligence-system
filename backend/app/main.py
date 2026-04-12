from flask import Flask, render_template
import pandas

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def show_info():
    dataFrame = pandas.read_csv("test.csv", sep="\t") 

    dataFrame = dataFrame[["step","type","amount","oldbalanceOrg","newbalanceOrig","oldbalanceDest","newbalanceDest",]]

    htmlFrame = dataFrame.to_html()
    return render_template("home.html", table=htmlFrame)
if __name__ == '__main__':
    app.run(debug=True)