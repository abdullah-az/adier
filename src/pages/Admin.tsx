import React, { useState, useEffect } from 'react';
import { Plus, X } from 'lucide-react';
import { المواد, الاسئلة } from '../lib/db';
import type { مادة, سؤال } from '../types/database';
import QuestionList from '../components/QuestionList';

const Admin = () => {
  const [المواد_المتاحة, setالمواد_المتاحة] = useState<مادة[]>([]);
  const [المادة_المحددة, setالمادة_المحددة] = useState<number | null>(null);
  const [اسئلة_المادة, setاسئلة_المادة] = useState<سؤال[]>([]);
  const [اضافة_سؤال, setاضافة_سؤال] = useState(false);
  const [السؤال_الجديد, setالسؤال_الجديد] = useState({
    نص_السؤال: '',
    الشرح: '',
    الخيارات: ['', '', '', ''],
    الاجابة_الصحيحة: 0
  });

  useEffect(() => {
    تحميل_المواد();
  }, []);

  useEffect(() => {
    if (المادة_المحددة) {
      تحميل_اسئلة_المادة(المادة_المحددة);
    }
  }, [المادة_المحددة]);

  const تحميل_المواد = async () => {
    const نتيجة = await المواد.الكل();
    setالمواد_المتاحة(نتيجة);
  };

  const تحميل_اسئلة_المادة = async (مادة_id: number) => {
    const نتيجة = await الاسئلة.حسب_المادة(مادة_id);
    setاسئلة_المادة(نتيجة);
  };

  const حفظ_سؤال = async () => {
    if (!المادة_المحددة) return;

    await الاسئلة.اضافة({
      نص_السؤال: السؤال_الجديد.نص_السؤال,
      الشرح: السؤال_الجديد.الشرح,
      المادة_id: المادة_المحددة,
      الخيارات: السؤال_الجديد.الخيارات.map((نص, index) => ({
        النص,
        صحيح: index === السؤال_الجديد.الاجابة_الصحيحة
      }))
    });

    setاضافة_سؤال(false);
    setالسؤال_الجديد({
      نص_السؤال: '',
      الشرح: '',
      الخيارات: ['', '', '', ''],
      الاجابة_الصحيحة: 0
    });
    
    if (المادة_المحددة) {
      تحميل_اسئلة_المادة(المادة_المحددة);
    }
  };

  const حذف_سؤال = async (id: number) => {
    await الاسئلة.حذف(id);
    if (المادة_المحددة) {
      تحميل_اسئلة_المادة(المادة_المحددة);
    }
  };

  const تعديل_سؤال = async (سؤال: سؤال) => {
    // سيتم تنفيذ التعديل في المرحلة القادمة
    console.log('تعديل السؤال:', سؤال);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="bg-white rounded-xl shadow-sm">
        {/* رأس الصفحة */}
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">إدارة الأسئلة</h1>
            <button
              onClick={() => setاضافة_سؤال(true)}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <Plus className="h-5 w-5 ml-2" />
              إضافة سؤال جديد
            </button>
          </div>
        </div>

        {/* اختيار المادة */}
        <div className="p-6 border-b">
          <select
            value={المادة_المحددة || ''}
            onChange={(e) => setالمادة_المحددة(Number(e.target.value))}
            className="w-full p-2 border rounded-lg"
          >
            <option value="">اختر المادة</option>
            {المواد_المتاحة.map((مادة) => (
              <option key={مادة.id} value={مادة.id}>
                {مادة.اسم}
              </option>
            ))}
          </select>
        </div>

        {/* قائمة الأسئلة */}
        <div className="p-6">
          {المادة_المحددة ? (
            <QuestionList
              الاسئلة={اسئلة_المادة}
              عند_التعديل={تعديل_سؤال}
              عند_الحذف={حذف_سؤال}
            />
          ) : (
            <div className="text-center text-gray-500">
              الرجاء اختيار مادة لعرض الأسئلة
            </div>
          )}
        </div>

        {/* نموذج إضافة سؤال */}
        {اضافة_سؤال && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-xl w-full max-w-2xl p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">إضافة سؤال جديد</h2>
                <button
                  onClick={() => setاضافة_سؤال(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">نص السؤال</label>
                  <textarea
                    value={السؤال_الجديد.نص_السؤال}
                    onChange={(e) => setالسؤال_الجديد(prev => ({ ...prev, نص_السؤال: e.target.value }))}
                    className="w-full border rounded-lg p-2 h-24"
                    placeholder="اكتب نص السؤال هنا..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">الخيارات</label>
                  {السؤال_الجديد.الخيارات.map((خيار, index) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={خيار}
                        onChange={(e) => {
                          const خيارات_جديدة = [...السؤال_الجديد.الخيارات];
                          خيارات_جديدة[index] = e.target.value;
                          setالسؤال_الجديد(prev => ({ ...prev, الخيارات: خيارات_جديدة }));
                        }}
                        className="flex-1 border rounded-lg p-2"
                        placeholder={`الخيار ${index + 1}`}
                      />
                      <button
                        onClick={() => setالسؤال_الجديد(prev => ({ ...prev, الاجابة_الصحيحة: index }))}
                        className={`px-4 py-2 rounded-lg ${
                          السؤال_الجديد.الاجابة_الصحيحة === index
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-100'
                        }`}
                      >
                        صحيح
                      </button>
                    </div>
                  ))}
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">الشرح</label>
                  <textarea
                    value={السؤال_الجديد.الشرح}
                    onChange={(e) => setالسؤال_الجديد(prev => ({ ...prev, الشرح: e.target.value }))}
                    className="w-full border rounded-lg p-2 h-24"
                    placeholder="اكتب شرح الإجابة هنا..."
                  />
                </div>

                <div className="flex justify-end gap-4 mt-6">
                  <button
                    onClick={() => setاضافة_سؤال(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                  >
                    إلغاء
                  </button>
                  <button
                    onClick={حفظ_سؤال}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    حفظ السؤال
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