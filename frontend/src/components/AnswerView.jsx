import { AlertCircle, CheckCircle, FileCode } from 'lucide-react';

export default function AnswerView({ answer, citations, error }) {
    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-5 shadow-sm">
                <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                        <h3 className="font-semibold text-red-900 mb-1">Error</h3>
                        <p className="text-red-700 text-sm">{error}</p>
                    </div>
                </div>
            </div>
        );
    }

    if (!answer) return null;

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            {/* AI Answer Section */}
            <div className="p-6 border-b border-gray-200">
                <div className="flex items-center gap-2 mb-4">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <h3 className="text-lg font-semibold text-gray-900">
                        Answer
                    </h3>
                </div>
                <div className="prose max-w-none">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                        {answer}
                    </p>
                </div>
            </div>

            {/* Citations Section */}
            {citations && citations.length > 0 && (
                <div className="p-6 bg-gray-50">
                    <div className="flex items-center gap-2 mb-4">
                        <FileCode className="w-5 h-5 text-blue-600" />
                        <h4 className="text-sm font-semibold text-gray-900">
                            Referenced Code
                        </h4>
                    </div>
                    <div className="space-y-2">
                        {citations.map((citation, index) => (
                            <div
                                key={index}
                                className="flex items-start gap-3 bg-white border border-gray-200 rounded-lg p-3 hover:border-blue-300 transition-colors"
                            >
                                <div className="flex items-center justify-center w-6 h-6 rounded bg-blue-600 text-white font-semibold text-xs flex-shrink-0">
                                    {index + 1}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="font-mono text-sm text-gray-700 truncate">
                                        {citation.file_path}
                                    </p>
                                    {citation.function_name && (
                                        <p className="text-sm text-gray-600 mt-1">
                                            Function: <code className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">{citation.function_name}</code>
                                        </p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
