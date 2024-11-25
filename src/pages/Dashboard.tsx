import React from 'react';
import { BarChart, Clock, Target, TrendingUp, Brain } from 'lucide-react';

const Dashboard = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-500 text-sm">Questions Attempted</h3>
            <Target className="h-6 w-6 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">248</div>
          <div className="text-sm text-green-600 flex items-center mt-2">
            <TrendingUp className="h-4 w-4 mr-1" />
            +12% this week
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-500 text-sm">Average Score</h3>
            <BarChart className="h-6 w-6 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">76%</div>
          <div className="text-sm text-green-600 flex items-center mt-2">
            <TrendingUp className="h-4 w-4 mr-1" />
            +5% this week
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-500 text-sm">Study Time</h3>
            <Clock className="h-6 w-6 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">18h 32m</div>
          <div className="text-sm text-green-600 flex items-center mt-2">
            <TrendingUp className="h-4 w-4 mr-1" />
            +2h this week
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-500 text-sm">AI Interactions</h3>
            <Brain className="h-6 w-6 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">156</div>
          <div className="text-sm text-green-600 flex items-center mt-2">
            <TrendingUp className="h-4 w-4 mr-1" />
            +8% this week
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="bg-white p-6 rounded-xl shadow-sm mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Performance Overview</h2>
        <div className="h-64 flex items-center justify-center text-gray-500">
          [Performance Chart Component - Displays subject-wise performance trends]
        </div>
      </div>

      {/* Recent Activity & Recommendations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Recent Activity */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Recent Activity</h2>
          <div className="space-y-4">
            {[
              {
                title: 'Completed Data Structures Quiz',
                time: '2 hours ago',
                score: '85%'
              },
              {
                title: 'AI Practice Session',
                time: '4 hours ago',
                score: '12 questions'
              },
              {
                title: 'Operating Systems Study',
                time: 'Yesterday',
                score: '2h 15m'
              }
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="font-medium text-gray-900">{activity.title}</h3>
                  <p className="text-sm text-gray-500">{activity.time}</p>
                </div>
                <div className="text-indigo-600 font-medium">{activity.score}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Recommended Topics</h2>
          <div className="space-y-4">
            {[
              {
                topic: 'Binary Search Trees',
                reason: 'Based on recent performance',
                difficulty: 'Medium'
              },
              {
                topic: 'Process Scheduling',
                reason: 'Upcoming in syllabus',
                difficulty: 'Hard'
              },
              {
                topic: 'Network Protocols',
                reason: 'Not attempted yet',
                difficulty: 'Easy'
              }
            ].map((topic, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg hover:border-indigo-600 transition-colors cursor-pointer">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-medium text-gray-900">{topic.topic}</h3>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    topic.difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
                    topic.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {topic.difficulty}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{topic.reason}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;