const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
    async ingestRepository(repoUrl) {
        const response = await fetch(`${API_BASE_URL}/api/v1/repository/ingest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ repo_url: repoUrl }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to ingest repository' }));
            throw new Error(error.detail || 'Failed to ingest repository');
        }

        return response.json();
    },

    async query(question, repoId) {
        const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question,
                repo_id: repoId,
                include_execution_flow: true
            }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to query' }));
            throw new Error(error.detail || 'Failed to query');
        }

        return response.json();
    },

    async getFile(filePath, repoId) {
        const response = await fetch(
            `${API_BASE_URL}/api/v1/file?file_path=${encodeURIComponent(filePath)}&repo_id=${repoId}`
        );

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to fetch file' }));
            throw new Error(error.detail || 'Failed to fetch file');
        }

        return response.json();
    },
};
