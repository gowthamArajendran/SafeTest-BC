from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from web3 import Web3
import warnings
import json
import solcx
import os
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = 'super_secret_secure_key_123'

# --- SQLITE Setup --- #
def init_db():
    conn = sqlite3.connect('exams.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS exams
                 (exam_code TEXT PRIMARY KEY, subject TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  exam_code TEXT, 
                  question_text TEXT, 
                  opt_a TEXT, opt_b TEXT, opt_c TEXT, opt_d TEXT, 
                  correct_opt TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS student_answers
                 (student_id TEXT, exam_code TEXT, question_id INTEGER, selected_option TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- WEB3 Config --- #
ganache_url = 'http://127.0.0.1:7545'
w3 = Web3(Web3.HTTPProvider(ganache_url))
contract_address = None
abi = None
bytecode = None

def compile_and_deploy_contract():
    global contract_address, abi, bytecode
    if not w3.is_connected():
        print("Warning: Could not connect to Ganache")
        return
    
    try:
        solcx.install_solc('0.8.0')
        with open('contracts/ExamStore.sol', 'r') as file:
            source_code = file.read()
            
        compiled_sol = solcx.compile_source(source_code, output_values=['abi', 'bin'], solc_version='0.8.0')
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']
        
        w3.eth.default_account = w3.eth.accounts[0]
        ExamStore = w3.eth.contract(abi=abi, bytecode=bytecode)
        print("Deploying Smart Contract...")
        tx_hash = ExamStore.constructor().transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        print(f"Contract deployed successfully at address: {contract_address}")
    except Exception as e:
        print(f"Error compiling/deploying: {e}")

compile_and_deploy_contract()

@app.route('/')
def home():
    session.clear()
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    
    if role == 'admin':
        admin_id = request.form.get('admin_id')
        password = request.form.get('password')
        if admin_id == 'admin' and password == 'admin123':
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid Admin Credentials!', 'danger')
            return redirect(url_for('home'))
            
    elif role == 'student':
        student_id = request.form.get('student_id')
        student_name = request.form.get('student_name')
        session['role'] = 'student'
        session['student_id'] = student_id
        session['student_name'] = student_name
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('home'))

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin.html')

@app.route('/configurator')
def configurator():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('configurator.html')

@app.route('/release_exam', methods=['POST'])
def release_exam():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.json
    subject = data.get('subject')
    questions = data.get('questions')
    
    if not questions or len(questions) == 0:
        return jsonify({'success': False, 'message': 'No questions added.'}), 400
        
    exam_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    conn = sqlite3.connect('exams.db')
    c = conn.cursor()
    c.execute('INSERT INTO exams (exam_code, subject) VALUES (?, ?)', (exam_code, subject))
    
    for q in questions:
        c.execute('''INSERT INTO questions (exam_code, question_text, opt_a, opt_b, opt_c, opt_d, correct_opt)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                  (exam_code, q['q_text'], q['opt_a'], q['opt_b'], q['opt_c'], q['opt_d'], q['correct_opt']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'exam_code': exam_code, 'subject': subject})

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('home'))
    return render_template('student.html')

@app.route('/get_exam/<exam_code>')
def get_exam(exam_code):
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = sqlite3.connect('exams.db')
    c = conn.cursor()
    c.execute('SELECT subject FROM exams WHERE exam_code = ?', (exam_code,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid Exam Code'}), 404
        
    subject = row[0]
    
    c.execute('SELECT id, question_text, opt_a, opt_b, opt_c, opt_d FROM questions WHERE exam_code = ?', (exam_code,))
    questions = []
    for q in c.fetchall():
        questions.append({
            'id': q[0], 
            'question_text': q[1], 
            'opt_a': q[2], 'opt_b': q[3], 'opt_c': q[4], 'opt_d': q[5]
        })
    conn.close()
    
    return jsonify({'success': True, 'subject': subject, 'questions': questions})

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.json
    exam_code = data.get('exam_code')
    answers = data.get('answers')
    student_id = session.get('student_id')
    student_name = session.get('student_name', 'Unknown')
    
    conn = sqlite3.connect('exams.db')
    c = conn.cursor()
    c.execute('SELECT subject FROM exams WHERE exam_code = ?', (exam_code,))
    subject_row = c.fetchone()
    if not subject_row:
        conn.close()
        return jsonify({'success': False, 'message': 'Exam code invalid'}), 400
        
    subject = subject_row[0]
    
    # Check if they have already submitted this exam locally
    c.execute('SELECT * FROM student_answers WHERE student_id = ? AND exam_code = ?', (student_id, exam_code))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'You have already submitted this exam! Record is immutable.'}), 400

    marks = 0
    total = len(answers) if answers else 0
    
    for ans in answers:
        q_id = ans['id']
        selected = ans['answer']
        
        # Save to local DB for review
        c.execute('INSERT INTO student_answers (student_id, exam_code, question_id, selected_option) VALUES (?, ?, ?, ?)',
                  (student_id, exam_code, q_id, selected))
                  
        c.execute('SELECT correct_opt FROM questions WHERE id = ?', (q_id,))
        correct = c.fetchone()[0]
        if selected == correct:
            marks += 1
            
    conn.commit()
    conn.close()
    
    if not contract_address or not abi:
        return jsonify({'success': False, 'message': 'Smart contract not deployed yet.'}), 500
        
    contract = w3.eth.contract(address=contract_address, abi=abi)
    key = f"{student_id}_{exam_code}"
    
    percent = int((marks / total) * 100) if total > 0 else 0
    
    try:
        tx_hash = contract.functions.addResult(key, student_id, student_name, exam_code, subject, percent).transact({'from': w3.eth.default_account})
        w3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        if "Result already exists" in str(e):
             return jsonify({'success': False, 'message': 'You have already submitted this exam! Record is immutable.'}), 400
        return jsonify({'success': False, 'message': f'Blockchain error: {e}'}), 500
        
    return jsonify({
        'success': True, 
        'message': 'Questions submitted successfully in student exam dashboard!',
        'marks': percent
    })

@app.route('/get_review/<exam_code>')
def get_review(exam_code):
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    student_id = session.get('student_id')
    conn = sqlite3.connect('exams.db')
    c = conn.cursor()
    
    c.execute('SELECT question_id, selected_option FROM student_answers WHERE student_id = ? AND exam_code = ?', (student_id, exam_code))
    answers = c.fetchall()
    
    if not answers:
        conn.close()
        return jsonify({'success': False, 'message': 'You have not submitted any answers for this Exam Code yet! You must finish the exam first to view results.'}), 404
        
    ans_dict = {row[0]: row[1] for row in answers}
    
    c.execute('SELECT id, question_text, opt_a, opt_b, opt_c, opt_d, correct_opt FROM questions WHERE exam_code = ?', (exam_code,))
    questions_data = []
    
    for q in c.fetchall():
        q_id = q[0]
        selected = ans_dict.get(q_id, 'Not Answered')
        questions_data.append({
            'question_text': q[1],
            'opt_a': q[2], 'opt_b': q[3], 'opt_c': q[4], 'opt_d': q[5],
            'correct_opt': q[6],
            'selected': selected,
            'is_correct': selected == q[6]
        })
        
    c.execute('SELECT subject FROM exams WHERE exam_code = ?', (exam_code,))
    subject = c.fetchone()[0]
    conn.close()
    
    return jsonify({'success': True, 'subject': subject, 'review_data': questions_data})

@app.route('/view_results')
def view_results():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
        
    results = []
    if contract_address and abi:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        try:
            keys = contract.functions.getAllKeys().call()
            for key in keys:
                res = contract.functions.getResult(key).call()
                results.append({
                    'studentID': res[0],
                    'studentName': res[1],
                    'examCode': res[2],
                    'subject': res[3],
                    'marks': res[4]
                })
        except Exception as e:
            flash(f"Error fetching from blockchain: {e}", "danger")
            
    return render_template('results.html', results=results)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
