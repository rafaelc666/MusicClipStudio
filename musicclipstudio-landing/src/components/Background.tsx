'use client';

import { useEffect, useState } from 'react';

type Tab = 'studio51' | 'musicclipstudio' | 'bluebookstudio' | 'agente009';

interface BackgroundProps {
  activeTab: Tab;
}

const backgroundImages = {
  studio51: [
    '/assets/images/studio51-set.jpeg', // Set de filmagem Studio 51
    '/assets/images/omega-interface.jpeg', // Interface OMEGA COMMAND
    '/assets/images/supernatural-hallway.jpeg', // Interior assombrado
  ],
  musicclipstudio: [
    '/assets/images/studio51-set.jpeg', // Set de filmagem (reutilizar)
    '/assets/images/bluebook-network.jpeg', // Rede de mídia (tem música)
    '/assets/images/omega-interface.jpeg', // Interface tecnológica
  ],
  bluebookstudio: [
    '/assets/images/bluebook-network.jpeg', // Rede de mídia interconectada
    '/assets/images/studio51-set.jpeg', // Set de filmagem (produção)
    '/assets/images/omega-interface.jpeg', // Interface tecnológica
  ],
  agente009: [
    '/assets/images/omega-interface.jpeg', // Interface OMEGA COMMAND
    '/assets/images/agente009-icon.jpeg', // Ícone lupa (放大 como background)
    '/assets/images/studio51-set.jpeg', // Set de filmagem (investigação)
  ],
};

export default function Background({ activeTab }: BackgroundProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const images = backgroundImages[activeTab] || backgroundImages.studio51;

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % images.length);
    }, 8000); // Troca a cada 8 segundos

    return () => clearInterval(interval);
  }, [activeTab, images.length]);

  return (
    <div className="fixed inset-0 -z-10">
      <div
        className="absolute inset-0 bg-cover bg-center transition-opacity duration-1000"
        style={{
          backgroundImage: `url(${images[currentImageIndex]})`,
          opacity: 0.15,
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-gray-900 via-gray-900/95 to-gray-900" />
      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-grid-pattern opacity-30" />
    </div>
  );
}