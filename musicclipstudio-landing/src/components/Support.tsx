'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export default function Support() {
  const { t } = useLanguage();

  return (
    <section id="support" className="py-20 px-4 bg-gradient-to-b from-gray-900 to-black">
      <div className="container mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {t.support.title}
          </h2>
          <p className="text-xl text-gray-300 mb-4">
            {t.support.subtitle}
          </p>
          <p className="text-lg text-gray-400 max-w-3xl mx-auto">
            {t.support.description}
          </p>
        </div>
        
        <div className="max-w-4xl mx-auto">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 mb-8 border border-gray-700">
            <h3 className="text-2xl font-bold text-white mb-4 text-center">
              {t.support.donation.title}
            </h3>
            <p className="text-xl text-amber-400 mb-6 text-center font-semibold">
              {t.support.donation.subtitle}
            </p>
            
            <div className="bg-gray-900/50 rounded-xl p-6 mb-6">
              <p className="text-gray-300 mb-4 text-center">
                {t.support.donation.description}
              </p>
              <ul className="space-y-2 mb-6">
                {t.support.donation.benefits.map((benefit, index) => (
                  <li key={index} className="flex items-start gap-2 text-gray-300">
                    <span className="text-amber-400 mt-1">✓</span>
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-gradient-to-br from-amber-900/20 to-amber-800/10 rounded-xl p-6 border border-amber-700/30">
              <h4 className="text-xl font-bold text-amber-400 mb-4 text-center">
                {t.support.donation.pix.title}
              </h4>
              <p className="text-gray-300 mb-4 text-center">
                {t.support.donation.pix.description}
              </p>
              <p className="text-gray-400 mb-6 text-center text-sm">
                {t.support.donation.pix.instructions}
              </p>
              
              <div className="flex flex-col items-center gap-4">
                <div className="bg-white p-4 rounded-lg">
                  {/* QR Code PIX para CPF 019.662.659-56 - Rafael Luis Campregher */}
                  <div className="w-48 h-48 bg-gray-100 flex items-center justify-center border-2 border-amber-600">
                    <div className="text-center">
                      <div className="text-6xl mb-2">📱</div>
                      <p className="text-gray-800 text-sm font-semibold">QR Code PIX</p>
                      <p className="text-gray-600 text-xs">019.662.659-56</p>
                      <p className="text-gray-500 text-xs mt-1">Rafael Luis Campregher</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-900 rounded-lg p-4 w-full max-w-md">
                  <p className="text-gray-400 text-sm mb-2 text-center">Chave PIX (CPF):</p>
                  <p className="text-amber-400 font-mono text-center text-lg mb-3">
                    019.662.659-56
                  </p>
                  <p className="text-gray-500 text-xs text-center mb-3">
                    Rafael Luis Campregher
                  </p>
                  <button 
                    className="w-full bg-amber-600 hover:bg-amber-700 text-white py-2 px-4 rounded-lg transition-colors text-sm font-semibold"
                    onClick={() => {
                      navigator.clipboard.writeText('01966265956');
                      alert('Chave PIX copiada!');
                    }}
                  >
                    Copiar Chave PIX
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-800/30 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-4 text-center">
              {t.support.donation.methods.title}
            </h3>
            
            <div className="text-center">
              <h4 className="text-lg font-semibold text-amber-400 mb-2">
                {t.support.donation.methods.email.title}
              </h4>
              <p className="text-gray-300 mb-3">
                {t.support.donation.methods.email.description}
              </p>
              <a
                href={`mailto:${t.contact.email}`}
                className="inline-block bg-gradient-to-r from-amber-600 to-amber-700 text-white py-3 px-6 rounded-lg font-semibold hover:from-amber-700 hover:to-amber-800 transition-all"
              >
                {t.contact.email}
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}