import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

const LanguageToggle = () => {
  const { i18n } = useTranslation();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ar' ? 'en' : 'ar';
    i18n.changeLanguage(newLang);
    document.dir = newLang === 'ar' ? 'rtl' : 'ltr';
  };

  return (
    <button
      onClick={toggleLanguage}
      className="flex items-center space-x-1 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
      aria-label="Toggle language"
    >
      <Globe className="h-5 w-5 text-gray-600" />
      <span className="text-sm font-medium text-gray-600">
        {i18n.language === 'ar' ? 'English' : 'العربية'}
      </span>
    </button>
  );
};

export default LanguageToggle;