import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { GraduationCap, Brain, BookOpen, LayoutDashboard, Settings } from 'lucide-react';
import LanguageToggle from './LanguageToggle';

const Navbar = () => {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;
  
  return (
    <nav className="bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <GraduationCap className="h-8 w-8 text-indigo-600" />
              <span className="font-bold text-xl text-gray-900">ExamPrep AI</span>
            </Link>
          </div>
          
          <div className="flex items-center space-x-8">
            <Link
              to="/"
              className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                isActive('/') 
                  ? 'text-indigo-600 border-b-2 border-indigo-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <BookOpen className="h-4 w-4 ml-1" />
              الرئيسية
            </Link>
            
            <Link
              to="/practice"
              className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                isActive('/practice')
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Brain className="h-4 w-4 ml-1" />
              التدريب
            </Link>
            
            <Link
              to="/ai-assistant"
              className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                isActive('/ai-assistant')
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Brain className="h-4 w-4 ml-1" />
              المساعد الذكي
            </Link>
            
            <Link
              to="/dashboard"
              className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                isActive('/dashboard')
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <LayoutDashboard className="h-4 w-4 ml-1" />
              لوحة التحكم
            </Link>

            <Link
              to="/admin"
              className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                isActive('/admin')
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Settings className="h-4 w-4 ml-1" />
              المسؤول
            </Link>

            <LanguageToggle />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;