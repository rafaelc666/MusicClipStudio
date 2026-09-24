'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export default function Header() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-gray-900/90 backdrop-blur-md border-b border-gray-800">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-amber-600 bg-gray-800">
            <img 
              src="/assets/images/studio51-logo.jpeg" 
              alt="Studio 51 Logo"
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <span className="font-bold text-xl text-white">Studio 51</span>
            <p className="text-xs text-amber-400">Ecossistema BlueBookStudio</p>
          </div>
        </div>
        
        <button
          onClick={() => setLanguage(language === 'pt' ? 'en' : 'pt')}
          className="px-4 py-2 rounded-lg bg-gray-800 text-white hover:bg-gray-700 transition-colors text-sm font-medium border border-gray-700 hover:border-amber-600"
        >
          {t.language.switch}
        </button>
      </div>
    </header>
  );
}