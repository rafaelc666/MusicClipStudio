'use client';

export default function BlueBookStudioContent() {
  return (
    <div className="min-h-screen pt-20">
      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <div className="inline-block mb-6 px-4 py-2 bg-blue-900/30 border border-blue-700/50 rounded-full">
            <span className="text-blue-400 text-sm font-medium">
              📚 BlueBookStudio - Tecnologia, Criatividade e História
            </span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
            BlueBookStudio
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-300 mb-4 font-light">
            Uma Suíte Completa de Criação com IA
          </p>
          
          <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
            BlueBookStudio é um ecossistema completo de ferramentas de criação usando inteligência artificial, abrangendo múltiplas formas de mídia e entretenimento.
          </p>
        </div>
      </section>

      {/* Ecossistema Visual */}
      <section className="py-20 px-4 bg-gray-800/30">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            Ecossistema Studio 51
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-amber-900/20 to-amber-800/10 rounded-xl overflow-hidden border border-amber-700/30">
              <div className="h-32 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/studio51-set.jpeg)' }} />
              <div className="p-4">
                <h3 className="text-xl font-bold text-white mb-2">Music Clip Studio</h3>
                <p className="text-gray-300 text-sm">
                  Transforme músicas em videoclipes com IA
                </p>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/10 rounded-xl overflow-hidden border border-blue-700/30">
              <div className="h-32 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/bluebook-network.jpeg)' }} />
              <div className="p-4">
                <h3 className="text-xl font-bold text-white mb-2">BlueBookStudio</h3>
                <p className="text-gray-300 text-sm">
                  Suíte completa de criação com IA
                </p>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 rounded-xl overflow-hidden border border-purple-700/30">
              <div className="h-32 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/omega-interface.jpeg)' }} />
              <div className="p-4">
                <h3 className="text-xl font-bold text-white mb-2">Agente 009</h3>
                <p className="text-gray-300 text-sm">
                  Sistema de investigação inteligente
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Serviços */}
      <section className="py-20 px-4">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            Serviços do Ecossistema
          </h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-blue-600/50 transition-all">
              <div className="text-4xl mb-4">🎬</div>
              <h3 className="text-xl font-bold text-white mb-2">Geração de Vídeos</h3>
              <p className="text-gray-300 text-sm">
                Criação automática de vídeos para YouTube com templates variados
              </p>
            </div>
            
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-blue-600/50 transition-all">
              <div className="text-4xl mb-4">📺</div>
              <h3 className="text-xl font-bold text-white mb-2">Documentários</h3>
              <p className="text-gray-300 text-sm">
                Pesquisa automática, roteiros informativos e narração via TTS
              </p>
            </div>
            
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-blue-600/50 transition-all">
              <div className="text-4xl mb-4">🎭</div>
              <h3 className="text-xl font-bold text-white mb-2">Séries e Novelas</h3>
              <p className="text-gray-300 text-sm">
                Criação de episódios em série com desenvolvimento de personagens
              </p>
            </div>
            
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-blue-600/50 transition-all">
              <div className="text-4xl mb-4">📚</div>
              <h3 className="text-xl font-bold text-white mb-2">Mangás e Gibis</h3>
              <p className="text-gray-300 text-sm">
                Geração de histórias em quadrinhos com múltiplos estilos
              </p>
            </div>
            
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-blue-600/50 transition-all">
              <div className="text-4xl mb-4">🎵</div>
              <h3 className="text-xl font-bold text-white mb-2">Music Clip Studio</h3>
              <p className="text-gray-300 text-sm">
                Transformação de músicas em videoclipes (já funcional)
              </p>
            </div>
            
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-blue-600/50 transition-all">
              <div className="text-4xl mb-4">🔧</div>
              <h3 className="text-xl font-bold text-white mb-2">Integração Total</h3>
              <p className="text-gray-300 text-sm">
                Serviços conectados com compartilhamento de recursos
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Roadmap */}
      <section className="py-20 px-4 bg-gray-800/30">
        <div className="container mx-auto max-w-4xl">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            Roadmap de Desenvolvimento
          </h2>
          
          <div className="space-y-4">
            <div className="bg-green-900/20 border border-green-700/30 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-green-400">✅</span>
                <h3 className="text-lg font-bold text-white">Fase 1: Music Clip Studio</h3>
              </div>
              <p className="text-gray-300 text-sm ml-6">
                MVP funcional, landing page, busca apoio para desenvolvimento
              </p>
            </div>
            
            <div className="bg-blue-900/20 border border-blue-700/30 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-blue-400">🔄</span>
                <h3 className="text-lg font-bold text-white">Fase 2: Integração Principal</h3>
              </div>
              <p className="text-gray-300 text-sm ml-6">
                Interface unificada, Documentário Engine, Video Engine básico
              </p>
            </div>
            
            <div className="bg-purple-900/20 border border-purple-700/30 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-purple-400">⏳</span>
                <h3 className="text-lg font-bold text-white">Fase 3: Expansão</h3>
              </div>
              <p className="text-gray-300 text-sm ml-6">
                Series/Soap Opera Engine, Manga/Comic Engine, Marketplace
              </p>
            </div>
            
            <div className="bg-amber-900/20 border border-amber-700/30 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-amber-400">🎯</span>
                <h3 className="text-lg font-bold text-white">Fase 4: Comunidade</h3>
              </div>
              <p className="text-gray-300 text-sm ml-6">
                API para desenvolvedores, plugins, comunidade ativa
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}