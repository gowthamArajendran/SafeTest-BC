# Full-Stack Blockchain-Based Secure Examination Management System

This project allows an admin to publish secure exam results to the Ethereum Blockchain (via a local Ganache node). Students are able to query their immutable records safely. The application is built using Python, Flask, Web3.py, and a Solidity Smart Contract.

## Prerequisites

1. **Python 3.8+**
2. **Ganache** (Download from [Truffle Suite](https://trufflesuite.com/ganache/))
3. **Microsoft Visual C++ Build Tools** (May be required by `py-solc-x` in Windows for compiling standard smart contracts if solc behaves unexpectedly).

## Setup Instructions

1. **Install Python Packages:**
   Open a terminal in this directory and execute:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Ganache Local Blockchain:**
   Open the **Ganache app**, and select "Quickstart Ethereum". Let it run in the background. It should establish an RPC server at `HTTP://127.0.0.1:7545`.

3. **Run the Flask Web App:**
   Inside this directory, run the Flask application:
   ```bash
   python app.py
   ```
   *Note: During the very first launch, the app might take a few moments as `py-solc-x` will attempt to fetch and install the correct Solidity compiler version (`0.8.0`) under the hood.*

## Usage

1. Open a Web browser and head comfortably to `http://127.0.0.1:5000/`.
2. **Admin Login:** Select "Administrator", enter ID: `admin`, Password: `admin123`.
3. You will be taken to the Blockchain Admin Panel where you can store Student Data safely. Submit a student's marks.
4. **Student View:** Logout, select "Student Profile", type in the Registration NO (e.g. `STU001`) from step 3. You will see your digitally preserved score!
