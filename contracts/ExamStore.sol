// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ExamStore {
    address public admin;

    struct Result {
        string studentID;
        string studentName;
        string examCode;
        string subject;
        uint256 marks;
        bool exists;
    }

    mapping(string => Result) private results;
    string[] public allResultKeys;

    event ResultAdded(string studentID, string studentName, string examCode, string subject, uint256 marks);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    function addResult(
        string memory _key, 
        string memory _studentID, 
        string memory _studentName,
        string memory _examCode, 
        string memory _subject, 
        uint256 _marks
    ) public onlyAdmin {
        require(!results[_key].exists, "Result already exists for this student and exam");
        
        results[_key] = Result({
            studentID: _studentID,
            studentName: _studentName,
            examCode: _examCode,
            subject: _subject,
            marks: _marks,
            exists: true
        });
        allResultKeys.push(_key);

        emit ResultAdded(_studentID, _studentName, _examCode, _subject, _marks);
    }

    function getResult(string memory _key) public view returns (string memory, string memory, string memory, string memory, uint256) {
        require(results[_key].exists, "Result not found");
        Result memory r = results[_key];
        return (r.studentID, r.studentName, r.examCode, r.subject, r.marks);
    }
    
    function getAllKeys() public view returns (string[] memory) {
        return allResultKeys;
    }
}
