import React, { useState } from 'react';
import { BookOpen, Clock, CheckCircle, XCircle } from 'lucide-react';

interface Question {
  id: number;
  text: string;
  options: string[];
  correctAnswer: number;
}

const Practice = () => {
  const [selectedSubject, setSelectedSubject] = useState('');
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  const subjects = [
    'Data Structures',
    'Algorithms',
    'Computer Architecture',
    'Operating Systems',
    'Database Systems',
    'Computer Networks'
  ];

  const sampleQuestion: Question = {
    id: 1,
    text: 'What is the time complexity of quicksort in the average case?',
    options: [
      'O(n)',
      'O(n log n)',
      'O(n²)',
      'O(log n)'
    ],
    correctAnswer: 1
  };

  const handleSubjectSelect = (subject: string) => {
    setSelectedSubject(subject);
    setCurrentQuestion(sampleQuestion);
    setSelectedAnswer(null);
    setShowExplanation(false);
  };

  const handleAnswerSelect = (index: number) => {
    setSelectedAnswer(index);
  };

  const handleSubmit = () => {
    setShowExplanation(true);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Subjects Sidebar */}
        <div className="bg-white p-6 rounded-xl shadow-sm h-fit">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <BookOpen className="h-5 w-5 mr-2 text-indigo-600" />
            Subjects
          </h2>
          <div className="space-y-2">
            {subjects.map((subject) => (
              <button
                key={subject}
                onClick={() => handleSubjectSelect(subject)}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  selectedSubject === subject
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {subject}
              </button>
            ))}
          </div>
        </div>

        {/* Question Area */}
        <div className="md:col-span-3">
          {!selectedSubject ? (
            <div className="bg-white p-8 rounded-xl shadow-sm text-center">
              <BookOpen className="h-12 w-12 text-indigo-600 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Select a Subject
              </h2>
              <p className="text-gray-600">
                Choose a subject from the sidebar to start practicing questions.
              </p>
            </div>
          ) : currentQuestion ? (
            <div className="space-y-8">
              {/* Timer and Progress */}
              <div className="bg-white p-4 rounded-xl shadow-sm flex justify-between items-center">
                <div className="flex items-center text-gray-600">
                  <Clock className="h-5 w-5 mr-2" />
                  <span>Time Remaining: 5:00</span>
                </div>
                <div className="text-gray-600">
                  Question 1 of 10
                </div>
              </div>

              {/* Question Card */}
              <div className="bg-white p-8 rounded-xl shadow-sm">
                <h3 className="text-xl font-semibold text-gray-900 mb-6">
                  {currentQuestion.text}
                </h3>
                <div className="space-y-4">
                  {currentQuestion.options.map((option, index) => (
                    <button
                      key={index}
                      onClick={() => handleAnswerSelect(index)}
                      className={`w-full p-4 rounded-lg border-2 text-left transition-colors ${
                        selectedAnswer === index
                          ? 'border-indigo-600 bg-indigo-50'
                          : 'border-gray-200 hover:border-indigo-600'
                      } ${
                        showExplanation
                          ? index === currentQuestion.correctAnswer
                            ? 'border-green-500 bg-green-50'
                            : selectedAnswer === index
                            ? 'border-red-500 bg-red-50'
                            : ''
                          : ''
                      }`}
                      disabled={showExplanation}
                    >
                      <div className="flex items-center justify-between">
                        <span>{option}</span>
                        {showExplanation && index === currentQuestion.correctAnswer && (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        )}
                        {showExplanation && selectedAnswer === index && index !== currentQuestion.correctAnswer && (
                          <XCircle className="h-5 w-5 text-red-500" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>

                {!showExplanation && selectedAnswer !== null && (
                  <button
                    onClick={handleSubmit}
                    className="mt-6 w-full py-3 px-4 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors"
                  >
                    Submit Answer
                  </button>
                )}

                {showExplanation && (
                  <div className="mt-8 p-6 bg-gray-50 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-2">Explanation</h4>
                    <p className="text-gray-600">
                      The average-case time complexity of quicksort is O(n log n). This occurs because, on average, 
                      the partition operation divides the array into roughly equal halves, leading to a balanced 
                      recursion tree with log n levels, and at each level, we perform O(n) comparisons.
                    </p>
                    <button
                      onClick={() => {
                        setCurrentQuestion(sampleQuestion);
                        setSelectedAnswer(null);
                        setShowExplanation(false);
                      }}
                      className="mt-4 py-2 px-4 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors"
                    >
                      Next Question
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default Practice;