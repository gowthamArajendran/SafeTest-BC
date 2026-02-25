from flask import Flask, render_template, request
from web3 import Web3
import json

# Static folder configuration
app = Flask(__name__, static_folder='static')

# Ganache Connection (Unga Current College IP)
# Intha IP correct-ah irukkannu oru thadava check pannikonga
ganache_ip = "http://172.20.36.125:7545" 
web3 = Web3(Web3.HTTPProvider(ganache_ip))

# Contract Configuration
contract_address = "0xBeCe3cc76A219148BEcbe9Cb834Cc2516d4cf3aa"
# Updated ABI to match your getResult function return types
abi = [
    {"inputs":[{"internalType":"uint256","name":"_studentId","type":"uint256"},{"internalType":"string","name":"_name","type":"string"},{"internalType":"uint256","name":"_marks","type":"uint256"}],"name":"addResult","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"_studentId","type":"uint256"}],"name":"getResult","outputs":[{"internalType":"string","name":"","type":"string"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]
contract = web3.eth.contract(address=contract_address, abi=abi)

# Global Variables for Exam State
questions_list = []
exam_duration = 10  
ADMIN_PASSWORD = "staff123"

@app.route('/')
def main_home():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    global questions_list, exam_duration
    error = None
    if request.method == 'POST':
        pw = request.form.get('password')
        if pw == ADMIN_PASSWORD:
            bulk_data = request.form.get('bulk_data')
            duration = request.form.get('duration')
            
            if bulk_data:
                try:
                    clean_data = bulk_data.replace('“', '"').replace('”', '"')
                    questions_list = json.loads(clean_data)
                    exam_duration = int(duration) if duration else 10
                    return render_template('redirect.html', msg=f"Success! {len(questions_list)} MCQs Released for {exam_duration} Mins! ✅")
                except Exception as e:
                    error = f"Invalid JSON format! Please use the Question Builder."
            return render_template('admin.html', login_mode=False, error=error)
    return render_template('admin.html', login_mode=True, error=error)

@app.route('/exam', methods=['GET', 'POST'])
def exam_portal():
    if request.method == 'POST':
        if 'student_submit' in request.form:
            s_id = request.form.get('id')
            s_name = request.form.get('name')
            return render_template('exam.html', questions=questions_list, id=s_id, name=s_name, duration=exam_duration, show_questions=True)
        
        elif 'final_submit' in request.form:
            try:
                s_id = int(request.form.get('id'))
                s_name = request.form.get('name')
                total_correct = 0
                
                for i, q in enumerate(questions_list):
                    ans = request.form.get(f'answer_{i}')
                    if ans and str(ans).strip().upper() == str(q['a']).strip().upper():
                        total_correct += 1
                
                marks = (total_correct * 100) // len(questions_list) if questions_list else 0

                # Submission - wait_for_transaction_receipt loading prachanaiya fix pannum
                tx_hash = contract.functions.addResult(s_id, s_name, marks).transact({'from': web3.eth.accounts[0]})
                web3.eth.wait_for_transaction_receipt(tx_hash)
                
                return render_template('redirect.html', msg=f"Exam Success! Marks: {marks}/100 recorded in Blockchain.")
            except Exception as e:
                print(f"CRITICAL BLOCKCHAIN ERROR: {e}") # Error-a terminal-la check panna
                return render_template('redirect.html', msg="Error: Ganache connection failed or Gas limit exceeded!")

    return render_template('exam.html', show_questions=False)

@app.route('/view_result', methods=['GET', 'POST'])
def result_view():
    res_data = None
    if request.method == 'POST':
        try:
            s_id = int(request.form.get('id'))
            blockchain_res = contract.functions.getResult(s_id).call()
            # Blockchain-la name empty-ah illana result-a kaatum
            if blockchain_res[0] != "":
                res_data = {"name": blockchain_res[0], "marks": blockchain_res[1], "id": s_id}
        except Exception as e:
            print(f"Result Fetch Error: {e}")
    return render_template('view_result.html', result=res_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)