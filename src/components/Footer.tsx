import React from 'react';
import { GraduationCap, Github, Mail } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-white border-t">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <GraduationCap className="h-6 w-6 text-indigo-600" />
              <span className="font-bold text-lg">ExamPrep AI</span>
            </div>
            <p className="text-gray-600 text-sm">
              Empowering computer engineering students with AI-powered exam preparation tools.
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>
                <a href="#" className="hover:text-indigo-600">About Us</a>
              </li>
              <li>
                <a href="#" className="hover:text-indigo-600">Privacy Policy</a>
              </li>
              <li>
                <a href="#" className="hover:text-indigo-600">Terms of Service</a>
              </li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Contact</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <a href="#" className="flex items-center hover:text-indigo-600">
                <Mail className="h-4 w-4 mr-2" />
                support@examprep.ai
              </a>
              <a href="#" className="flex items-center hover:text-indigo-600">
                <Github className="h-4 w-4 mr-2" />
                GitHub Repository
              </a>
            </div>
          </div>
        </div>
        
        <div className="mt-8 pt-8 border-t text-center text-sm text-gray-500">
          <p>&copy; {new Date().getFullYear()} ExamPrep AI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;