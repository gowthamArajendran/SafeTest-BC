// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MultiExamSystem {
    struct ExamSet {
        string questionsJson;
        uint256 duration;
        address creator;
    }

    struct StudentResult {
        string name;
        uint256 marks;
        bool exists;
    }

    // Exam Code -> Exam Details (Questions & Time)
    mapping(string => ExamSet) private exams;
    
    // Exam Code -> (Student ID -> Result)
    mapping(string => mapping(uint256 => StudentResult)) private results;

    // Staff logic: Exam create panni questions-a Blockchain-la lock panna
    function createExam(string memory _code, string memory _json, uint256 _duration) public {
        exams[_code] = ExamSet(_json, _duration, msg.sender);
    }

    // Student logic: Exam code kuduthu questions fetch panna
    function getExam(string memory _code) public view returns (string memory, uint256) {
        return (exams[_code].questionsJson, exams[_code].duration);
    }

    // Marks-a andha specific exam code kela store panna
    function addResult(string memory _code, uint256 _studentId, string memory _name, uint256 _marks) public {
        results[_code][_studentId] = StudentResult(_name, _marks, true);
    }

    // Results fetch panna
    function getResult(string memory _code, uint256 _studentId) public view returns (string memory, uint256) {
        require(results[_code][_studentId].exists, "Result not found");
        return (results[_code][_studentId].name, results[_code][_studentId].marks);
    }
}