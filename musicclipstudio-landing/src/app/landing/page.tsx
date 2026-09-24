'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import Background from '@/components/Background';
import Hero from '@/components/Hero';
import Features from '@/components/Features';
import Support from '@/components/Support';
import Contact from '@/components/Contact';
import Footer from '@/components/Footer';
import Studio51Content from '@/components/Studio51Content';
import BlueBookStudioContent from '@/components/BlueBookStudioContent';
import Agente009Content from '@/components/Agente009Content';

type Tab = 'studio51' | 'musicclipstudio' | 'bluebookstudio' | 'agente009';

// O metadata desta página fica em ./layout.tsx (esta é client component).

/**
 * Página de MARKETING multi-produto (Studio 51 / MusicClipStudio /
 * BlueBookStudio / Agente009).
 *
 * ⚠️ Ela NÃO fica mais na raiz. A raiz "/" redireciona para /studio (o
 * programa), porque quem abre este app quer usar o gerador de clipes — não
 * ler a página de vendas. Esta landing vive em /landing.
 */
export default function LandingPage() {
  const [activeTab, setActiveTab] = useState<Tab>('studio51');

  const renderContent = () => {
    switch (activeTab) {
      case 'studio51':
        return <Studio51Content />;
      case 'musicclipstudio':
        return (
          <>
            <Hero />
            <Features />
            <Support />
            <Contact />
          </>
        );
      case 'bluebookstudio':
        return <BlueBookStudioContent />;
      case 'agente009':
        return <Agente009Content />;
      default:
        return <Studio51Content />;
    }
  };

  return (
    <div className="min-h-screen bg-black">
      <Background activeTab={activeTab} />
      <Header />
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
      <main>
        {renderContent()}
      </main>
      <Footer />
    </div>
  );
}
