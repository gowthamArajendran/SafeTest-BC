// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ExamResult {
    struct Result {
        string studentName;
        uint256 marks;
    }

    mapping(uint256 => Result) public results;

    function addResult(uint256 _studentId, string memory _name, uint256 _marks) public {
        results[_studentId] = Result(_name, _marks);
    }

    function getResult(uint256 _studentId) public view returns (string memory, uint256) {
        return (results[_studentId].studentName, results[_studentId].marks);
    }
}