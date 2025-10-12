
import os
from flask import Flask, render_template, request, url_for, send_from_directory, redirect
from app.config import OUTPUTS_DIR
from app.graph.builder import build_graph

app = Flask(__name__, template_folder='ui/templates', static_folder='ui/static')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_research():
    query = request.form.get('query') or ''
    ticker = request.form.get('ticker') or None
    mode = (request.form.get('mode') or 'Normal').lower()
    # Modes
    if mode == 'strict':
        os.environ['REQUIRE_TOPIC_TERMS'] = 'true'
        os.environ['MIN_EVIDENCE_OVERLAP'] = '2'
        os.environ['STRICT_VERIFICATION'] = 'true'
    elif mode == 'relaxed':
        os.environ['REQUIRE_TOPIC_TERMS'] = 'false'
        os.environ['MIN_EVIDENCE_OVERLAP'] = '1'
        os.environ['STRICT_VERIFICATION'] = 'false'
    else:
        os.environ['REQUIRE_TOPIC_TERMS'] = 'true'
        os.environ['MIN_EVIDENCE_OVERLAP'] = '1'
        os.environ['STRICT_VERIFICATION'] = 'true'

    graph = build_graph()
    final = graph.invoke({'query': query, 'ticker': ticker})
    report_path = final.get('report_html')
    if not report_path or not os.path.exists(report_path):
        return 'No report produced.', 500
    filename = os.path.basename(report_path)
    return redirect(url_for('outputs_file', filename=filename), code=302)

@app.route('/outputs/<path:filename>')
def outputs_file(filename):
    return send_from_directory(OUTPUTS_DIR, filename)

@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools_probe():
    return app.response_class("{}", mimetype='application/json')

if __name__ == '__main__':
    app.run(port=5011, debug=True)
