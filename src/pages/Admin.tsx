import React, { useState, useEffect } from 'react';
import { Plus, X } from 'lucide-react';
import { subjects, questions } from '../lib/db';
import type { Subject, Question } from '../types/database';
import QuestionList from '../components/QuestionList';

const Admin = () => {
  const [subjectsAvailable, setSubjectsAvailable] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<number | null>(null);
  const [subjectQuestions, setSubjectQuestions] = useState<Question[]>([]);
  const [addQuestion, setAddQuestion] = useState(false);
  const [newQuestion, setNewQuestion] = useState({
    text: '',
    explanation: '',
    options: ['', '', '', ''],
    correctAnswer: 0
  });

  useEffect(() => {
    loadSubjects();
  }, []);

  useEffect(() => {
    if (selectedSubject) {
      loadSubjectQuestions(selectedSubject);
    }
  }, [selectedSubject]);

  const loadSubjects = async () => {
    const result = await subjects.findAll();
    setSubjectsAvailable(result);
  };

  const loadSubjectQuestions = async (subjectId: number) => {
    const result = await questions.findBySubjectId(subjectId);
    setSubjectQuestions(result);
  };

  const saveQuestion = async () => {
    if (!selectedSubject) return;

    await questions.create({
      text: newQuestion.text,
      explanation: newQuestion.explanation,
      subjectId: selectedSubject,
      options: newQuestion.options.map((text, index) => ({
        text,
        isCorrect: index === newQuestion.correctAnswer
      }))
    });

    setAddQuestion(false);
    setNewQuestion({
      text: '',
      explanation: '',
      options: ['', '', '', ''],
      correctAnswer: 0
    });

    if (selectedSubject) {
      loadSubjectQuestions(selectedSubject);
    }
  };

  const deleteQuestion = async (id: number) => {
    await questions.delete(id);
    if (selectedSubject) {
      loadSubjectQuestions(selectedSubject);
    }
  };

  const editQuestion = async (question: Question) => {
    // Edit functionality will be implemented in a future step
    console.log('Edit question:', question);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="bg-white rounded-xl shadow-sm">
        {/* Page header */}
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Manage Questions</h1>
            <button
              onClick={() => setAddQuestion(true)}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <Plus className="h-5 w-5 ml-2" />
              Add New Question
            </button>
          </div>
        </div>

        {/* Subject selection */}
        <div className="p-6 border-b">
          <select
            value={selectedSubject || ''}
            onChange={(e) => setSelectedSubject(Number(e.target.value))}
            className="w-full p-2 border rounded-lg"
          >
            <option value="">Select Subject</option>
            {subjectsAvailable.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </select>
        </div>

        {/* Question list */}
        <div className="p-6">
          {selectedSubject ? (
            <QuestionList
              questions={subjectQuestions}
              onEdit={editQuestion}
              onDelete={deleteQuestion}
            />
          ) : (
            <div className="text-center text-gray-500">
              Please select a subject to view questions
            </div>
          )}
        </div>

        {/* Add question form */}
        {addQuestion && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-xl w-full max-w-2xl p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">Add New Question</h2>
                <button
                  onClick={() => setAddQuestion(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Question Text</label>
                  <textarea
                    value={newQuestion.text}
                    onChange={(e) => setNewQuestion(prev => ({ ...prev, text: e.target.value }))}
                    className="w-full border rounded-lg p-2 h-24"
                    placeholder="Enter question text here..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Options</label>
                  {newQuestion.options.map((option, index) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={option}
                        onChange={(e) => {
                          const newOptions = [...newQuestion.options];
                          newOptions[index] = e.target.value;
                          setNewQuestion(prev => ({ ...prev, options: newOptions }));
                        }}
                        className="flex-1 border rounded-lg p-2"
                        placeholder={`Option ${index + 1}`}
                      />
                      <button
                        onClick={() => setNewQuestion(prev => ({ ...prev, correctAnswer: index }))}
                        className={`px-4 py-2 rounded-lg ${
                          newQuestion.correctAnswer === index
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-100'
                        }`}
                      >
                        Correct
                      </button>
                    </div>
                  ))}
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Explanation</label>
                  <textarea
                    value={newQuestion.explanation}
                    onChange={(e) => setNewQuestion(prev => ({ ...prev, explanation: e.target.value }))}
                    className="w-full border rounded-lg p-2 h-24"
                    placeholder="Enter explanation here..."
                  />
                </div>

                <div className="flex justify-end gap-4 mt-6">
                  <button
                    onClick={() => setAddQuestion(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveQuestion}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    Save Question
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;
