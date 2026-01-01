import { FileCode } from 'lucide-react';

export default function CodeViewer({ filePath, code, language = 'javascript', highlightedLines = [] }) {
    if (!code) return null;

    const lines = code.split('\n');

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            {/* File Path Header */}
            <div className="bg-gray-800 px-4 py-3 border-b border-gray-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <FileCode className="w-4 h-4 text-blue-400" />
                        <span className="font-mono text-sm text-gray-100">{filePath}</span>
                    </div>
                    <span className="px-2 py-1 bg-blue-600 text-white text-xs font-medium uppercase rounded">
                        {language}
                    </span>
                </div>
            </div>

            {/* Code Content */}
            <div className="bg-gray-900 text-gray-100 overflow-x-auto">
                <div className="flex">
                    {/* Line Numbers */}
                    <div className="bg-gray-800 text-gray-500 text-right px-4 py-4 select-none">
                        {lines.map((_, index) => (
                            <div
                                key={index}
                                className={`font-mono text-xs leading-6 ${highlightedLines.includes(index + 1) ? 'text-yellow-400' : ''
                                    }`}
                            >
                                {index + 1}
                            </div>
                        ))}
                    </div>

                    {/* Code Lines */}
                    <div className="flex-1 px-4 py-4 overflow-x-auto">
                        {lines.map((line, index) => (
                            <div
                                key={index}
                                className={`font-mono text-sm leading-6 ${highlightedLines.includes(index + 1)
                                        ? 'bg-yellow-500/20 -mx-4 px-4'
                                        : ''
                                    }`}
                            >
                                <code>{line || ' '}</code>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
