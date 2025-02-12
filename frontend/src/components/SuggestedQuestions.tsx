import React from 'react';
import { Home, Briefcase, Heart, Scale, Leaf, BookOpen } from 'lucide-react';

interface SuggestedQuestionsProps {
  onQuestionClick: (question: string) => void;
}

const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({ onQuestionClick }) => {
  const suggestions = [
    {
      title: "Vivienda",
      icon: <Home className="w-5 h-5" />,
      questions: [
        "¿Qué partidos proponen aumentar la oferta de vivienda social?",
        "¿Qué medidas se proponen para mejorar el acceso a la vivienda?"
      ]
    },
    {
      title: "Empleo",
      icon: <Briefcase className="w-5 h-5" />,
      questions: [
        "¿Qué políticas hay para mejorar la calidad del empleo?",
        "¿Qué propuestas tienen para fomentar el emprendidmiento?"
      ]
    },
    {
      title: "Sanidad",
      icon: <Heart className="w-5 h-5" />,
      questions: [
        "¿Qué planes tienen los partidos para reducir las listas de espera en hospitales?",
        "¿Qué partidos apuestan por reforzar la sanidad pública?"
      ]
    },
    {
      title: "Fiscalidad",
      icon: <Scale className="w-5 h-5" />,
      questions: [
        "¿Qué partidos proponen subir o bajar impuestos?",
        "¿Cómo planean financiar el gasto público?"
      ]
    },
    {
      title: "Medio Ambiente",
      icon: <Leaf className="w-5 h-5" />,
      questions: [
        "¿Qué medidas hay para combatir el cambio climático?",
        "¿Cómo se planea impulsar las energías renovables?"
      ]
    },
    {
      title: "Educación",
      icon: <BookOpen className="w-5 h-5" />,
      questions: [
        "¿Qué cambios proponen en el sistema educativo?",
        "¿Qué partidos apoyan la educación gratuita en universidades?"
      ]
    }
  ];

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">
          ¿Sobre qué te gustaría preguntar?
        </h2>
        <p className="text-gray-600">
          Selecciona una pregunta o escribe la tuya propia
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {suggestions.map((category) => (
          <div key={category.title} 
               className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-4 bg-blue-50 border-b border-gray-100 flex items-center gap-2">
              <span className="text-blue-600">
                {category.icon}
              </span>
              <h3 className="font-medium text-gray-800">
                {category.title}
              </h3>
            </div>
            <div className="p-4 space-y-3">
              {category.questions.map((question) => (
                <button
                  key={question}
                  onClick={() => onQuestionClick(question)}
                  className="w-full text-left p-3 rounded-lg text-gray-700 hover:bg-blue-50 
                           transition-colors duration-200 ease-in-out hover:text-blue-700
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SuggestedQuestions;