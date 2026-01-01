import { GitCommit } from 'lucide-react';

export default function FlowView({ steps }) {
    if (!steps || steps.length === 0) return null;

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <div className="flex items-center gap-2 mb-6">
                <GitCommit className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">
                    Execution Flow
                </h3>
            </div>

            <div className="space-y-3">
                {steps.map((step, index) => (
                    <div key={index} className="flex gap-4">
                        {/* Step Number */}
                        <div className="flex flex-col items-center">
                            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600 text-white font-semibold text-sm">
                                {index + 1}
                            </div>
                            {index < steps.length - 1 && (
                                <div className="w-0.5 bg-blue-200 flex-1 mt-2"></div>
                            )}
                        </div>

                        {/* Step Content */}
                        <div className="flex-1 pb-4">
                            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                                <h4 className="font-semibold text-gray-900 mb-1">
                                    {step.function_name || step.name}
                                </h4>
                                {step.file_path && (
                                    <p className="font-mono text-xs text-gray-600 mb-2">
                                        {step.file_path}
                                    </p>
                                )}
                                {step.description && (
                                    <p className="text-sm text-gray-700 mt-2">
                                        {step.description}
                                    </p>
                                )}
                                {step.params && (
                                    <div className="mt-2 text-xs">
                                        <span className="text-gray-600">Parameters: </span>
                                        <code className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{step.params}</code>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
