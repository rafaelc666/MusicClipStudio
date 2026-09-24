'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export default function Hero() {
  const { t } = useLanguage();

  return (
    <section className="pt-32 pb-20 px-4 bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 min-h-screen flex items-center">
      <div className="container mx-auto text-center">
        <div className="inline-block mb-6 px-4 py-2 bg-amber-900/30 border border-amber-700/50 rounded-full">
          <span className="text-amber-400 text-sm font-medium">
            🎵 Studio 51 - BlueBookStudio
          </span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
          {t.hero.title}
        </h1>
        
        <p className="text-xl md:text-2xl text-gray-300 mb-4 font-light">
          {t.hero.subtitle}
        </p>
        
        <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
          {t.hero.description}
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="/studio"
            className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-sky-600 text-[#06141a] rounded-full font-semibold hover:from-cyan-400 hover:to-sky-500 transition-all transform hover:scale-105 shadow-lg shadow-cyan-900/50 relative group overflow-hidden"
          >
            <span className="relative z-10 inline-flex items-center gap-2">
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              {t.hero.cta} · Studio Web
            </span>
            <span className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/30 to-transparent group-hover:translate-x-full transition-transform duration-700" />
          </a>
          <a
            href="#features"
            className="px-8 py-4 text-white rounded-full font-semibold border-2 border-gray-700 hover:border-cyan-500/70 hover:bg-white/[0.02] transition-all"
          >
            Saiba Mais
          </a>
        </div>

        <div className="mt-16 grid grid-cols-3 gap-8 max-w-2xl mx-auto opacity-50">
          <div className="text-center">
            <div className="text-3xl mb-2">🎬</div>
            <p className="text-gray-400 text-sm">IA Avançada</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">🎵</div>
            <p className="text-gray-400 text-sm">Áudio Original</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">🚀</div>
            <p className="text-gray-400 text-sm">Gratuito</p>
          </div>
        </div>
      </div>
    </section>
  );
}