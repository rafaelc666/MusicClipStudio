'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="py-8 px-4 bg-black border-t border-gray-800">
      <div className="container mx-auto text-center">
        <p className="text-gray-400 mb-2">
          {t.footer.copyright}
        </p>
        <p className="text-sm text-gray-500 mb-2">
          {t.footer.developedBy}
        </p>
        <p className="text-xs text-amber-600 font-semibold">
          {t.footer.studio51}
        </p>
      </div>
    </footer>
  );
}