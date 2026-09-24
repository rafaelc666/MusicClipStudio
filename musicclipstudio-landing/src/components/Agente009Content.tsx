'use client';

export default function Agente009Content() {
  return (
    <div className="min-h-screen pt-20">
      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <div className="inline-block mb-6 px-4 py-2 bg-purple-900/30 border border-purple-700/50 rounded-full">
            <span className="text-purple-400 text-sm font-medium">
              🕵️ Agente 009 - Sistema de Investigação Inteligente
            </span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
            AGENTE 009
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-300 mb-4 font-light">
            Investigação Automatizada com Inteligência Artificial
          </p>
          
          <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
            Um sistema avançado de investigação e análise de informações usando IA, parte integrante do ecossistema BlueBookStudio.
          </p>
        </div>
</section>

      {/* Sobre o Sistema */}
      <section className="py-20 px-4 bg-gray-800/30">
        <div className="container mx-auto max-w-4xl">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            Sobre o Agente 009
          </h2>
          
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700">
            <p className="text-gray-300 mb-4">
              Agente 009 é um sistema especializado em investigação automatizada, projetado para analisar informações, detectar padrões e gerar insights usando técnicas avançadas de inteligência artificial.
            </p>
            <p className="text-gray-300 mb-4">
              Integrado ao ecossistema BlueBookStudio, o Agente 009 auxilia na pesquisa de conteúdo para documentários, análise de teorias conspiratórias, e investigação de mistérios e fenômenos inexplicáveis.
            </p>
            <p className="text-gray-300">
              Com capacidades de processamento de linguagem natural, análise de dados e geração de relatórios, o sistema atua como um assistente de investigação poderoso e eficiente.
            </p>
          </div>
        </div>
      </section>

      {/* Funcionalidades */}
      <section className="py-20 px-4">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            Funcionalidades
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 rounded-xl overflow-hidden border border-purple-700/30">
              <div className="h-24 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/omega-interface.jpeg)' }} />
              <div className="p-4">
                <h3 className="text-xl font-bold text-white mb-2">Pesquisa Automatizada</h3>
                <p className="text-gray-300 text-sm">
                  Busca e análise automática de informações em múltiplas fontes
                </p>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 rounded-xl overflow-hidden border border-purple-700/30">
              <div className="h-24 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/agente009-icon.jpeg)' }} />
              <div className="p-4">
                <h3 className="text-xl font-bold text-white mb-2">Análise de Padrões</h3>
                <p className="text-gray-300 text-sm">
                  Detecção de padrões e correlações em grandes volumes de dados
                </p>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 rounded-xl overflow-hidden border border-purple-700/30">
              <div className="h-24 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/omega-interface.jpeg)' }} />
              <div className="p-4">
                <h3 className="text-xl font-bold text-white mb-2">Geração de Relatórios</h3>
                <p className="text-gray-300 text-sm">
                  Criação automática de relatórios detalhados e sumários executivos
                </p>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 rounded-xl overflow-hidden border border-purple-700/30">
              <div className="h-24 bg-cover bg-center" style={{ backgroundImage: 'url(/assets/images/bluebook-network.jpeg)' }} />
              <div className="p-4">
                <h3 className="text-xl font-bold text-white mb-2">IA Contextual</h3>
                <p className="text-gray-300 text-sm">
                  Compreensão contextual de informações e geração de insights
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Status */}
      <section className="py-20 px-4 bg-gray-800/30">
        <div className="container mx-auto max-w-4xl">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">
            Status do Projeto
          </h2>
          
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-amber-400 text-2xl">⏳</span>
              <h3 className="text-xl font-bold text-white">Em Desenvolvimento</h3>
            </div>
            <p className="text-gray-300 mb-4">
              O Agente 009 está atualmente em fase de desenvolvimento e planejamento. Integração completa com o ecossistema BlueBookStudio está prevista para as fases futuras do roadmap.
            </p>
            <div className="bg-purple-900/20 border border-purple-700/30 rounded-lg p-4">
              <p className="text-purple-300 text-sm">
                <strong>Próximos Passos:</strong> Desenvolvimento do core engine, integração com APIs de pesquisa, e criação de interface de usuário.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}