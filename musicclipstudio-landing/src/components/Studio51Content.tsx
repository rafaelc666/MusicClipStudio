'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export default function Studio51Content() {
  return (
    <div className="min-h-screen pt-20">
      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <div className="inline-block mb-6 px-4 py-2 bg-amber-900/30 border border-amber-700/50 rounded-full">
            <span className="text-amber-400 text-sm font-medium">
              🛸 Studio 51 - Onde os Mistérios Viram Filme
            </span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
            STUDIO 51
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-300 mb-4 font-light">
            O Extraordinário Também É Real
          </p>
          
          <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
            Um canal de YouTube dedicado ao extraordinário, ao inexplicável e ao fascinante mundo dos mistérios, UFOs, teorias conspiratórias e o supernatural.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto mt-12">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl overflow-hidden border border-gray-700 hover:border-amber-600/50 transition-all group">
              <div className="h-24 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/ufo-icon.jpeg)' }} />
              <div className="p-3">
                <p className="text-white font-semibold text-sm">UFO</p>
              </div>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl overflow-hidden border border-gray-700 hover:border-amber-600/50 transition-all group">
              <div className="h-24 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/omega-interface.jpeg)' }} />
              <div className="p-3">
                <p className="text-white font-semibold text-sm">Teorias</p>
              </div>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl overflow-hidden border border-gray-700 hover:border-amber-600/50 transition-all group">
              <div className="h-24 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/studio51-set.jpeg)' }} />
              <div className="p-3">
                <p className="text-white font-semibold text-sm">Documentários</p>
              </div>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl overflow-hidden border border-gray-700 hover:border-amber-600/50 transition-all group">
              <div className="h-24 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/supernatural-hallway.jpeg)' }} />
              <div className="p-3">
                <p className="text-white font-semibold text-sm">Supernatural</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Sobre o Canal */}
      <section className="py-20 px-4 bg-gray-800/30">
        <div className="container mx-auto max-w-4xl">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            Sobre o Studio 51
          </h2>
          
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700">
            <p className="text-gray-300 mb-4">
              Studio 51 não é apenas um canal - é a casa oficial do ecossistema BlueBookStudio. Aqui investigamos, criamos e demonstramos o que é possível com inteligência artificial.
            </p>
            <p className="text-gray-300 mb-4">
              Nossa missão é democratizar a criação de conteúdo profissional enquanto exploramos os mistérios do universo, usando tecnologia de ponta para transformar o extraordinário em conteúdo cinematográfico.
            </p>
            <p className="text-gray-300">
              Através do Studio 51, você encontrará documentários investigativos, tutoriais das ferramentas BlueBookStudio, demonstrações de capacidades criativas e muito mais.
            </p>
          </div>
        </div>
      </section>

      {/* Ecossistema */}
      <section className="py-20 px-4">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            Ecossistema Studio 51
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-amber-900/20 to-amber-800/10 rounded-xl p-6 border border-amber-700/30">
              <div className="text-4xl mb-4">🎵</div>
              <h3 className="text-xl font-bold text-white mb-2">Music Clip Studio</h3>
              <p className="text-gray-300 text-sm">
                Transforme músicas em videoclipes com IA
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/10 rounded-xl p-6 border border-blue-700/30">
              <div className="text-4xl mb-4">📚</div>
              <h3 className="text-xl font-bold text-white mb-2">BlueBookStudio</h3>
              <p className="text-gray-300 text-sm">
                Suíte completa de criação com IA
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 rounded-xl p-6 border border-purple-700/30">
              <div className="text-4xl mb-4">🕵️</div>
              <h3 className="text-xl font-bold text-white mb-2">Agente 009</h3>
              <p className="text-gray-300 text-sm">
                Sistema de investigação inteligente
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}