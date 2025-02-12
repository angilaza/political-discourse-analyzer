import React from 'react';
import { Info } from 'lucide-react';

const ProgramsNotice: React.FC = () => {
  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4 flex items-center gap-3">
      <Info className="text-yellow-600 w-6 h-6" />
      <p className="text-yellow-800 text-sm">
        El asistente puede responder preguntas basadas en los programas electorales de
        <strong> PSOE, PP, VOX, Sumar, ERC, Junts y Bildu</strong>. Las respuestas se generan a partir de estos documentos.
      </p>
    </div>
  );
};

export default ProgramsNotice;