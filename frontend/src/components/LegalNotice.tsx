import { useEffect, useState } from 'react';
import { AlertTriangle } from 'lucide-react';

const LegalNotice = () => {
    const [showNotice, setShowNotice] = useState(true);

    useEffect(() => {
        const hasSeenNotice = localStorage.getItem('hasSeenLegalNotice');
        setShowNotice(!hasSeenNotice);
    }, []);

    const handleAccept = () => {
        localStorage.setItem('hasSeenLegalNotice', 'true');
        setShowNotice(false);
    };

    if (!showNotice) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Overlay */}
            <div className="fixed inset-0 bg-black bg-opacity-50" />

            {/* Modal */}
            <div className="relative z-50 w-[90vw] max-w-[500px] rounded-lg bg-white p-6 shadow-lg">
                <div className="flex items-center gap-2 text-lg font-semibold text-gray-900">
                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                    <h2>Aviso Importante</h2>
                </div>

                <div className="mt-4 space-y-4 text-sm text-gray-600">
                    <p>
                        Esta aplicación forma parte de un proyecto universitario de investigación que utiliza la versión Beta de OpenAI Assistants API.
                    </p>

                    <p>
                        <strong>Aspectos importantes a considerar:</strong>
                    </p>

                    <ul className="list-disc pl-5 space-y-2">
                        <li>Las respuestas pueden contener imprecisiones o errores debido a la naturaleza experimental de la tecnología.</li>
                        <li>Todas las interacciones son almacenadas de forma anónima y serán utilizadas exclusivamente con fines de investigación académica.</li>
                        <li>No se recopila información personal identificable.</li>
                    </ul>

                    <p className="text-xs text-gray-500 mt-4">
                        Al continuar usando esta aplicación, aceptas estas condiciones y el uso de tus interacciones para fines de investigación.
                    </p>
                </div>

                <div className="mt-6 flex justify-end">
                    <button
                        onClick={handleAccept}
                        className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        Entendido, continuar
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LegalNotice;