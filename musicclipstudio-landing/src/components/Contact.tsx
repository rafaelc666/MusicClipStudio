'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export default function Contact() {
  const { t } = useLanguage();

  return (
    <section className="py-20 px-4 bg-white dark:bg-black">
      <div className="container mx-auto text-center">
        <h2 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
          {t.contact.title}
        </h2>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
          {t.contact.description}
        </p>
        
        <a
          href={`mailto:${t.contact.email}`}
          className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full font-semibold hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 shadow-lg"
        >
          <span>📧</span>
          {t.contact.email}
        </a>
      </div>
    </section>
  );
}