import React from 'react';
import { Edit2, Trash2 } from 'lucide-react';
import type { سؤال } from '../types/database';

interface QuestionListProps {
  الاسئلة: سؤال[];
  عند_التعديل: (سؤال: سؤال) => void;
  عند_الحذف: (id: number) => void;
}

const QuestionList: React.FC<QuestionListProps> = ({ الاسئلة, عند_التعديل, عند_الحذف }) => {
  return (
    <div className="space-y-4">
      {الاسئلة.map((سؤال) => (
        <div key={سؤال.id} className="border rounded-lg p-4 hover:border-indigo-600 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="font-medium text-gray-900">{سؤال.نص_السؤال}</h3>
            </div>
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => عند_التعديل(سؤال)}
                className="p-2 text-gray-600 hover:text-indigo-600"
              >
                <Edit2 className="h-5 w-5" />
              </button>
              <button 
                onClick={() => عند_الحذف(سؤال.id)}
                className="p-2 text-gray-600 hover:text-red-600"
              >
                <Trash2 className="h-5 w-5" />
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {سؤال.الخيارات?.map((خيار) => (
              <div
                key={خيار.id}
                className={`p-2 rounded ${
                  خيار.صحيح
                    ? 'bg-green-100 border border-green-500'
                    : 'bg-gray-50'
                }`}
              >
                {خيار.النص}
              </div>
            ))}
          </div>
          {سؤال.الشرح && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">{سؤال.الشرح}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default QuestionList;