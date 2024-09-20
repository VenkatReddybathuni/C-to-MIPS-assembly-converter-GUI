from flask import Flask, render_template, request
from mips_translator import translate_to_mips_advanced

app = Flask(__name__)

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        c_code = request.form['c_code']
        assembly_code = translate_to_mips_advanced(c_code)
        return render_template('index.html', assembly_code=assembly_code, c_code=c_code)
    return render_template('index.html', assembly_code='', c_code='')

if __name__ == '__main__':
    app.run(debug=True)
