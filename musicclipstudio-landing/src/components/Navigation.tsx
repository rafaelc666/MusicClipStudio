'use client';

import { useLanguage } from '@/contexts/LanguageContext';

type Tab = 'studio51' | 'musicclipstudio' | 'bluebookstudio' | 'agente009';

interface NavigationProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

export default function Navigation({ activeTab, onTabChange }: NavigationProps) {
  const { t } = useLanguage();

  const tabs = [
    { id: 'studio51' as Tab, label: 'Studio 51', icon: '🛸', image: '/assets/images/ufo-icon.jpeg' },
    { id: 'musicclipstudio' as Tab, label: 'Music Clip Studio', icon: '🎵', image: '/assets/images/ufo-icon.jpeg' },
    { id: 'bluebookstudio' as Tab, label: 'BlueBookStudio', icon: '📚', image: '/assets/images/bluebook-network.jpeg' },
    { id: 'agente009' as Tab, label: 'Agente 009', icon: '🕵️', image: '/assets/images/agente009-icon.jpeg' },
  ];

  return (
    <nav className="fixed top-16 left-0 right-0 z-40 bg-gray-900/95 backdrop-blur-md border-b border-gray-800">
      <div className="container mx-auto px-4">
        <div className="flex gap-2 py-3 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-amber-600 text-white shadow-lg shadow-amber-900/50'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <div className="w-6 h-6 rounded-full overflow-hidden bg-gray-700 flex items-center justify-center">
                {tab.image ? (
                  <img 
                    src={tab.image} 
                    alt={tab.label}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span>{tab.icon}</span>
                )}
              </div>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}