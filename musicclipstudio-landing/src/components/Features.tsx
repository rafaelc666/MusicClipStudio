'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export default function Features() {
  const { t } = useLanguage();

  const features = [
    {
      icon: '🤖',
      title: t.features.feature1.title,
      description: t.features.feature1.description
    },
    {
      icon: '🎬',
      title: t.features.feature2.title,
      description: t.features.feature2.description
    },
    {
      icon: '🎵',
      title: t.features.feature3.title,
      description: t.features.feature3.description
    },
    {
      icon: '🎨',
      title: t.features.feature4.title,
      description: t.features.feature4.description
    },
    {
      icon: '🚀',
      title: t.features.feature5.title,
      description: t.features.feature5.description
    }
  ];

  return (
    <section id="features" className="py-20 px-4 bg-gray-900">
      <div className="container mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {t.features.title}
          </h2>
          <p className="text-xl text-gray-300">
            {t.features.subtitle}
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="p-6 bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700 hover:border-amber-600/50 transition-all transform hover:-translate-y-2"
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-300">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}