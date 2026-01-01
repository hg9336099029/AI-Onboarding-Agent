import { useState } from 'react';
import { Sparkles, CheckCircle2, Loader2, Loader, Send, User, Bot, Clock } from 'lucide-react';
import CodeViewer from '../components/CodeViewer';
import FlowView from '../components/FlowView';
import { api } from '../services/api';

export default function Home() {
    const [isLoading, setIsLoading] = useState(false);
    const [repoUrl, setRepoUrl] = useState('');
    const [question, setQuestion] = useState('');
    const [loadingStage, setLoadingStage] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [error, setError] = useState(null);
    const [repoId, setRepoId] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();

        // First, ingest the repository if we don't have a repoId
        if (!repoId && repoUrl.trim()) {
            setIsLoading(true);
            setError(null);
            setLoadingStage('Cloning repository...'); // Start ingestion stage

            try {
                // Simulate progress stages for ingestion
                // In a real application, these stages would be reported by the backend
                const ingestionPromise = api.ingestRepository(repoUrl);

                // Simulate progress updates
                const progressInterval = setInterval(() => {
                    setLoadingStage(prevStage => {
                        if (prevStage === 'Cloning repository...') return 'Parsing code...';
                        if (prevStage === 'Parsing code...') return 'Generating embeddings...';
                        if (prevStage === 'Generating embeddings...') return 'Storing data...';
                        return prevStage; // Keep the last stage if no new one
                    });
                }, 3000); // Update every 3 seconds

                const response = await ingestionPromise;
                clearInterval(progressInterval); // Stop interval on success
                setRepoId(response.repo_id);
                setLoadingStage(''); // Clear stage after successful ingestion
            } catch (err) {
                setError(err.message || 'Failed to load repository. Please check the URL and try again.');
                setIsLoading(false);
                setLoadingStage(''); // Clear stage on error
                return;
            }
        }

        // Then ask the question if we have one
        if (question.trim()) {
            if (!repoId && !repoUrl.trim()) {
                setError('Please provide a repository URL first.');
                return;
            }

            // Add user question to history
            const userMessage = {
                type: 'user',
                content: question,
                timestamp: new Date().toLocaleTimeString()
            };

            setChatHistory(prev => [...prev, userMessage]);
            const currentQuestion = question;
            setQuestion(''); // Clear input immediately
            setIsLoading(true);
            setError(null);

            try {
                const response = await api.query(currentQuestion, repoId);

                // Add AI response to history
                const aiMessage = {
                    type: 'ai',
                    content: response.answer,
                    citations: response.citations || [],
                    codeView: response.code_snippet,
                    flowSteps: response.execution_flow,
                    timestamp: new Date().toLocaleTimeString()
                };

                setChatHistory(prev => [...prev, aiMessage]);
            } catch (err) {
                setError(err.message || 'Failed to get answer. Please try again.');
            } finally {
                setIsLoading(false);
            }
        } else {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-8 py-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-blue-600 p-2 rounded-lg">
                            <Sparkles className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">
                                AI Codebase Onboarding
                            </h1>
                            <p className="text-gray-600 text-sm">
                                Understand any codebase instantly with AI
                            </p>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-8 py-6">
                {/* Input Form */}
                <div className="mb-6 sticky top-24 z-10">
                    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-lg">
                        <form onSubmit={handleSubmit}>
                            {/* Repository URL Input */}
                            <div className="mb-4">
                                <label className="block text-sm font-semibold text-gray-900 mb-2">
                                    Repository URL
                                </label>
                                <input
                                    type="text"
                                    value={repoUrl}
                                    onChange={(e) => setRepoUrl(e.target.value)}
                                    placeholder="https://github.com/username/repository"
                                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    disabled={isLoading || repoId}
                                />
                                {repoId && (
                                    <p className="mt-2 text-xs text-green-600 flex items-center gap-1">
                                        <CheckCircle2 className="w-3 h-3" />
                                        Repository loaded
                                    </p>
                                )}
                            </div>

                            {/* Question Input */}
                            <div className="mb-4">
                                <label className="block text-sm font-semibold text-gray-900 mb-2">
                                    Ask a Question
                                </label>
                                <input
                                    type="text"
                                    value={question}
                                    onChange={(e) => setQuestion(e.target.value)}
                                    placeholder="Ask about this codebase..."
                                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    disabled={isLoading}
                                />
                            </div>

                            {/* Submit Button */}
                            <div className="flex justify-center">
                                <button
                                    type="submit"
                                    disabled={isLoading || (!repoUrl.trim() && !repoId) || !question.trim()}
                                    className="px-6 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            <span>Processing...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Send className="w-4 h-4" />
                                            <span>Send Question</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                )}

                {/* Chat History */}
                {chatHistory.length > 0 && (
                    <div className="space-y-4 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                            <Clock className="w-5 h-5 text-blue-600" />
                            Conversation History
                        </h2>

                        {chatHistory.map((message, index) => (
                            <div key={index}>
                                {message.type === 'user' ? (
                                    // User Message
                                    <div className="flex gap-3 items-start">
                                        <div className="bg-blue-600 p-2 rounded-full flex-shrink-0">
                                            <User className="w-4 h-4 text-white" />
                                        </div>
                                        <div className="flex-1">
                                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                                <p className="text-sm text-gray-900">{message.content}</p>
                                            </div>
                                            <p className="text-xs text-gray-500 mt-1 ml-1">{message.timestamp}</p>
                                        </div>
                                    </div>
                                ) : (
                                    // AI Message
                                    <div className="flex gap-3 items-start">
                                        <div className="bg-green-600 p-2 rounded-full flex-shrink-0">
                                            <Bot className="w-4 h-4 text-white" />
                                        </div>
                                        <div className="flex-1">
                                            <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                                                <p className="text-sm text-gray-900 whitespace-pre-wrap leading-relaxed">
                                                    {message.content}
                                                </p>

                                                {/* Citations */}
                                                {message.citations && message.citations.length > 0 && (
                                                    <div className="mt-4 pt-4 border-t border-gray-200">
                                                        <h4 className="text-xs font-semibold text-gray-700 mb-2">Referenced Code</h4>
                                                        <div className="space-y-2">
                                                            {message.citations.map((citation, idx) => (
                                                                <div key={idx} className="flex items-start gap-2 bg-gray-50 p-2 rounded text-xs">
                                                                    <span className="bg-blue-600 text-white w-5 h-5 rounded flex items-center justify-center flex-shrink-0 font-semibold">
                                                                        {idx + 1}
                                                                    </span>
                                                                    <div className="flex-1 min-w-0">
                                                                        <p className="font-mono text-gray-700 truncate">{citation.file_path}</p>
                                                                        {citation.function_name && (
                                                                            <p className="text-gray-600 mt-1">
                                                                                Function: <code className="bg-blue-100 text-blue-700 px-1 rounded">{citation.function_name}</code>
                                                                            </p>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                            <p className="text-xs text-gray-500 mt-1 ml-1">{message.timestamp}</p>

                                            {/* Code View */}
                                            {message.codeView && (
                                                <div className="mt-3">
                                                    <CodeViewer
                                                        filePath={message.codeView.file_path}
                                                        code={message.codeView.code}
                                                        language={message.codeView.language}
                                                        highlightedLines={message.codeView.highlighted_lines}
                                                    />
                                                </div>
                                            )}

                                            {/* Flow Steps */}
                                            {message.flowSteps && message.flowSteps.length > 0 && (
                                                <div className="mt-3">
                                                    <FlowView steps={message.flowSteps} />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Loading State */}
                {isLoading && loadingStage && (
                    <div className="bg-white rounded-lg shadow-md p-8 text-center">
                        <div className="flex flex-col items-center space-y-4">
                            <Loader className="w-12 h-12 text-blue-600 animate-spin" />
                            <div className="space-y-2">
                                <p className="text-lg font-semibold text-gray-800">
                                    {loadingStage}
                                </p>
                                <p className="text-sm text-gray-600">
                                    {loadingStage === 'Cloning repository...' && 'Downloading code from GitHub'}
                                    {loadingStage === 'Parsing code...' && 'Analyzing Python files with AST'}
                                    {loadingStage === 'Generating embeddings...' && 'Creating vector representations (this may take a few minutes)'}
                                    {loadingStage === 'Storing data...' && 'Saving to database'}
                                    {!['Cloning repository...', 'Parsing code...', 'Generating embeddings...', 'Storing data...'].includes(loadingStage) && 'Processing your repository...'}
                                </p>
                                <p className="text-xs text-gray-500 mt-4">
                                    💡 First time? Model download (~90MB) may take 2-5 minutes
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Welcome Screen */}
                {chatHistory.length === 0 && !isLoading && (
                    <div className="text-center py-12">
                        <Sparkles className="mx-auto h-16 w-16 text-blue-600 mb-4" />
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            Get Started
                        </h2>
                        <p className="text-gray-600 max-w-lg mx-auto mb-8">
                            Enter a repository URL and ask a question to get AI-powered insights about the codebase.
                        </p>

                        {/* Example Questions */}
                        {repoId && (
                            <div className="max-w-2xl mx-auto">
                                <p className="text-sm font-medium text-gray-700 mb-3 flex items-center justify-center gap-2">
                                    <Sparkles className="w-4 h-4 text-blue-600" />
                                    Try these example questions
                                </p>
                                <div className="space-y-2">
                                    {[
                                        'What does the authentication flow look like?',
                                        'How is user data stored in the database?',
                                        'Explain the API routing structure',
                                    ].map((example, index) => (
                                        <button
                                            key={index}
                                            onClick={() => setQuestion(example)}
                                            className="w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all text-sm text-gray-700"
                                        >
                                            {example}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
