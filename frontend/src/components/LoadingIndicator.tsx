import { Loader2 } from 'lucide-react';

const LoadingIndicator = () => {
  return (
    <div className="flex items-center justify-start p-4 space-x-3 bg-gray-50 rounded-lg max-w-3xl">
      <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
      <p className="text-sm text-gray-600">
        Analizando tu consulta...
      </p>
    </div>
  );
};

export default LoadingIndicator;