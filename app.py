from flask import Flask, render_template, request
from web3 import Web3
import json
import random
import string

app = Flask(__name__, static_folder='static')

# Ganache Connection - Localhost stable-ah irukkum
ganache_ip = "http://127.0.0.1:7545" 
web3 = Web3(Web3.HTTPProvider(ganache_ip))

# Contract Configuration
contract_address = "0x9bC7dFe382Eb1c64f9C13B7Fb423DAa39Eb5b9eb" 
abi = [
    {"inputs":[{"internalType":"string","name":"_code","type":"string"},{"internalType":"string","name":"_json","type":"string"},{"internalType":"uint256","name":"_duration","type":"uint256"}],"name":"createExam","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"string","name":"_code","type":"string"}],"name":"getExam","outputs":[{"internalType":"string","name":"","type":"string"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"string","name":"_code","type":"string"},{"internalType":"uint256","name":"_studentId","type":"uint256"},{"internalType":"string","name":"_name","type":"string"},{"internalType":"uint256","name":"_marks","type":"uint256"}],"name":"addResult","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"string","name":"_code","type":"string"},{"internalType":"uint256","name":"_studentId","type":"uint256"}],"name":"getResult","outputs":[{"internalType":"string","name":"","type":"string"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]
contract = web3.eth.contract(address=contract_address, abi=abi)

ADMIN_PASSWORD = "staff123"

# IPPO IDHU THAAN FIRST LOAD AAGUM
@app.route('/')
def main_home():
    return render_template('index.html') 

# Home page-la student login form trigger aaga
@app.route('/student_login')
def student_login():
    return render_template('index.html') 

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    error = None
    if request.method == 'POST':
        pw = request.form.get('password')
        if pw == ADMIN_PASSWORD:
            bulk_data = request.form.get('bulk_data')
            duration = request.form.get('duration')
            if bulk_data:
                try:
                    # Random 6-digit Code Generation
                    exam_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    clean_data = bulk_data.replace('“', '"').replace('”', '"')
                    duration_val = int(duration) if duration else 10
                    
                    # Blockchain-la questions-a store pannum
                    contract.functions.createExam(exam_code, clean_data, duration_val).transact({
                        'from': web3.eth.accounts[0], 'gas': 3000000
                    })
                    return render_template('redirect.html', msg=f"✅ Exam Released! Code: {exam_code}")
                except Exception as e:
                    error = "Blockchain storage failed!"
            return render_template('admin.html', login_mode=False, error=error)
    return render_template('admin.html', login_mode=True, error=error)

@app.route('/exam', methods=['GET', 'POST'])
def exam_portal():
    if request.method == 'POST':
        if 'student_submit' in request.form:
            s_id = request.form.get('id'); s_name = request.form.get('name')
            e_code = request.form.get('exam_code').strip().upper()
            try:
                # Blockchain-la irundhu questions-a fetch pannum
                blockchain_data = contract.functions.getExam(e_code).call()
                if blockchain_data[0] == "": return render_template('redirect.html', msg="❌ Invalid Code!")
                questions = json.loads(blockchain_data[0]); duration = blockchain_data[1]
                return render_template('exam.html', questions=questions, id=s_id, name=s_name, duration=duration, exam_code=e_code, show_questions=True)
            except Exception: return render_template('redirect.html', msg="Error fetching exam data!")
        
        elif 'final_submit' in request.form:
            try:
                s_id = int(request.form.get('id')); s_name = request.form.get('name'); e_code = request.form.get('exam_code')
                blockchain_data = contract.functions.getExam(e_code).call()
                questions = json.loads(blockchain_data[0]); total_correct = 0
                for i, q in enumerate(questions):
                    ans = request.form.get(f'answer_{i}')
                    if ans and str(ans).strip().upper() == str(q['a']).strip().upper(): total_correct += 1
                marks = (total_correct * 100) // len(questions) if questions else 0
                
                # Ledger-la marks-a record pannum
                contract.functions.addResult(e_code, s_id, s_name, marks).transact({'from': web3.eth.accounts[0], 'gas': 2000000})
                return render_template('redirect.html', msg=f"🎉 Success! Marks: {marks}/100 recorded.")
            except Exception: return render_template('redirect.html', msg="Submission failed!")
    
    return render_template('exam.html', show_questions=False)

@app.route('/view_result', methods=['GET', 'POST'])
def result_view():
    res_data = None
    if request.method == 'POST':
        try:
            s_id = int(request.form.get('id')); e_code = request.form.get('exam_code').strip().upper()
            blockchain_res = contract.functions.getResult(e_code, s_id).call()
            if blockchain_res[0] != "": res_data = {"name": blockchain_res[0], "marks": blockchain_res[1], "id": s_id, "code": e_code}
        except Exception: return render_template('redirect.html', msg="Result not found!")
    return render_template('view_result.html', result=res_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)