# Project Limitations
## AI Codebase Onboarding Assistant

This document outlines the current limitations, constraints, and known issues of the AI Codebase Onboarding Assistant.

---

### 1. Language Support

#### 1.1 Supported Languages
Currently, the system supports AST parsing and code understanding for:
- ✅ **Python** (full support)
- ✅ **JavaScript** (full support)
- ⚠️ **TypeScript** (experimental - treated  as JavaScript)

#### 1.2 Unsupported Languages
The following languages are **not yet supported**:
- ❌ Java
- ❌ C/C++
- ❌ Go
- ❌ Rust
- ❌ Ruby
- ❌ PHP
- ❌ Kotlin
- ❌ Swift

**Impact:** Files in unsupported languages will be skipped during ingestion, and the system cannot answer questions about them.

**Workaround:** Focus analysis on supported languages within multi-language repositories.

---

### 2. Repository Constraints

#### 2.1 Repository Size
- **Maximum file size:** 10 MB per file (configurable via `MAX_FILE_SIZE_MB`)
- **Recommended repository size:** < 500 MB
- **Large repository performance:** Ingestion time increases linearly with repository size

**Impact:** Very large monorepos (> 1 GB) may take significant time to ingest and process.

**Workaround:**
- Clone specific subdirectories or branches
- Increase timeout settings for large repos
- Use `.gitignore` patterns to exclude non-essential files

#### 2.2 Private Repositories
- **Current support:** Public repositories only
- **Authentication:** Not yet implemented for private repos

**Impact:** Cannot clone private GitHub/GitLab repositories.

**Workaround:**
- Manually clone private repos to local filesystem
- Point ingestion service to local path
- Future: Add SSH key or token-based authentication

#### 2.3 Repository Types
- **Supported:** Git repositories (GitHub, GitLab, Bitbucket)
- **Unsupported:** SVN, Mercurial, or other VCS

---

### 3. Code Analysis Limitations

#### 3.1 AST Parsing Accuracy
- **Python:** ~95% accuracy for standard Python code
- **JavaScript:** ~90% accuracy for modern ES6+ code
- **Complex macros/metaprogramming:** May not parse correctly

**Known Issues:**
- Dynamically generated code cannot be analyzed
- Heavy use of decorators/metaclasses may cause parsing errors
- Minified JavaScript is not parsed effectively

#### 3.2 Execution Flow Analysis
- **Maximum depth:** 5 levels (configurable via `MAX_FLOW_DEPTH`)
- **Recursive functions:** May not fully trace beyond depth limit
- **Dynamic dispatch:** Cannot resolve runtime polymorphism
- **Third-party libraries:** External dependencies not analyzed

**Example Limitation:**
```python
# Cannot trace beyond library boundary
import external_lib
result = external_lib.magic_function()  # Execution flow stops here
```

#### 3.3 Semantic Understanding
- **Context window:** Limited by LLM's token limit (~8K for Llama 3.1)
- **Cross-file reasoning:** May miss connections across distant files
- **Domain-specific logic:** AI may not understand specialized algorithms

---

### 4. Performance Limitations

#### 4.1 Ingestion Speed
| Repository Size | Estimated Time |
|----------------|----------------|
| < 50 files | 1-2 minutes |
| 100-500 files | 5-10 minutes |
| 500-1000 files | 15-30 minutes |
| > 1000 files | 30+ minutes |

**Factors affecting speed:**
- Number of files
- Average file size
- Embedding provider (HuggingFace slower than OpenAI)
- Hardware (CPU, RAM)

#### 4.2 Query Response Time
- **Simple queries:** < 2 seconds
- **Execution flow queries:** 3-5 seconds
- **Complex multi-file queries:** 5-10 seconds

**Bottlenecks:**
- LLM API latency (Groq: ~1-3 seconds)
- Vector search complexity (scales with corpus size)
- Database metadata lookups

#### 4.3 Concurrent Users
- **Current architecture:** Single-user deployment
- **Concurrency:** Limited to API thread pool (default: 10 workers)

**Impact:** Not suitable for team-wide deployment without infrastructure scaling.

---

### 5. LLM and Embedding Limitations

#### 5.1 LLM Provider (Groq)
- **Rate limits:** Free tier has request/minute limits
- **Model availability:** Subject to Groq's service uptime
- **Context limit:** ~8,000 tokens for Llama 3.1

**Known Issues:**
- Occasional API timeouts during peak usage
- Rate limit errors during heavy querying
- Model changes may affect response quality

#### 5.2 Embedding Provider
**HuggingFace (Free):**
- ✅ No API costs
- ❌ Slower than OpenAI (CPU-based)
- ❌ Lower accuracy for specialized code

**OpenAI (Paid):**
- ✅ Fast and accurate
- ❌ Costs money ($0.0001/1K tokens)
- ❌ Requires API key

#### 5.3 Accuracy Limitations
- **Hallucinations:** LLM may generate incorrect information (5-10% error rate)
- **Citation errors:** Occasionally cites wrong file/line numbers
- **Context loss:** Long answers may lose coherence

**Mitigation:**
- Always verify answers against actual code
- Use citations to cross-check LLM responses
- Lower temperature (0.1) for more deterministic answers

---

### 6. Database and Storage Limitations

#### 6.1 PostgreSQL
- **Connection limit:** Default 100 concurrent connections
- **Storage:** Grows with number of repositories ingested
- **Backup:** No automated backup system

#### 6.2 FAISS Vector Store
- **In-memory index:** Requires RAM proportional to embedding count
- **Persistence:** Manual save required (auto-save on shutdown)
- **Scalability:** Limited to single machine's RAM

**Estimated Memory Usage:**
| Chunks | Dimension | Memory |
|--------|-----------|--------|
| 10,000 | 384 | ~15 MB |
| 100,000 | 384 | ~150 MB |
| 1,000,000 | 384 | ~1.5 GB |

#### 6.3 File System
- **Repository storage:** Cloned repos consume disk space
- **No automatic cleanup:** Old repos must be manually deleted

---

### 7. Security Limitations

#### 7.1 Authentication & Authorization
- ❌ No user authentication system
- ❌ No role-based access control
- ❌ All users can access all repositories

**Impact:** Suitable only for single-user or trusted team environments.

#### 7.2 Code Privacy
- ⚠️ Code snippets sent to Groq API for LLM inference
- ⚠️ Subject to Groq's data privacy policies
- ⚠️ Not suitable for highly sensitive codebases

**Recommendation:** Use self-hosted LLMs for confidential code.

#### 7.3 Input Validation
- ✅ Git URL validation implemented
- ⚠️ Limited file type validation
- ❌ No sandboxing for malicious code

**Risk:** Malicious repositories could potentially exploit parsing vulnerabilities.

---

### 8. Frontend Limitations

#### 8.1 User Interface
- **Basic UI:** Minimal feature set
- **No code editor:** Cannot edit code directly
- **Limited visualization:** Basic execution flow diagrams only

#### 8.2 Browser Compatibility
- **Tested:** Chrome, Firefox, Edge (latest versions)
- **Untested:** Safari, mobile browsers
- **Requirement:** JavaScript enabled

#### 8.3 Responsiveness
- **Desktop-optimized:** Not fully mobile-responsive
- **Small screens:** May have layout issues

---

### 9. Deployment Limitations

#### 9.1 Docker Deployment
- **Resource requirements:**
  - Minimum: 4 GB RAM, 2 CPU cores
  - Recommended: 8 GB RAM, 4 CPU cores
- **Storage:** 20+ GB for Docker images and repositories

#### 9.2 Production Readiness
- ❌ No horizontal scaling support
- ❌ No load balancer configuration
- ❌ No monitoring/alerting built-in
- ❌ No automated backups

**Current Status:** Suitable for development and small-scale personal use only.

---

### 10. Known Issues

#### 10.1 AST Parsing
- **Issue:** Python decorators with complex arguments may fail to parse
- **Workaround:** None currently
- **Status:** Tracked in backlog

#### 10.2 Vector Store
- **Issue:** FAISS index requires manual save after ingestion
- **Workaround:** Ensure graceful shutdown or manual save
- **Status:** Auto-save on shutdown implemented

#### 10.3 Error Handling
- **Issue:** Repository ingestion errors not always surfaced to user
- **Workaround:** Check backend logs for detailed errors
- **Status:** Improving error propagation in progress

#### 10.4 Cross-Platform
- **Issue:** File path handling differs between Windows/Linux
- **Workaround:** Use Docker for consistent environment
- **Status:** Testing on both platforms

---

### 11. Future Improvements

#### Planned Features
- ✅ Multi-language support (Java, Go, Rust)
- ✅ Private repository authentication
- ✅ Multi-user support with authentication
- ✅ Self-hosted LLM option (Ollama, vLLM)
- ✅ IDE integration (VSCode extension)
- ✅ Real-time repository monitoring
- ✅ Advanced visualization (interactive call graphs)
- ✅ Code generation capabilities

#### Feature Requests
See GitHub Issues for community-requested features.

---

### 12. Support and Troubleshooting

#### Common Issues

**Problem:** Repository ingestion fails
- **Check:** Repository URL is valid and public
- **Check:** Disk space available
- **Check:** Supported language files exist

**Problem:** Slow query responses
- **Check:** LLM API is responsive (Groq status)
- **Check:** Vector store is loaded
- **Check:** Database connection is active

**Problem:** Inaccurate answers
- **Check:** Repository was fully ingested
- **Check:** Question is clear and specific
- **Check:** Relevant code exists in repository

#### Getting Help
- **Documentation:** See `/docs` folder
- **Logs:** Check `backend/logs` for detailed errors
- **GitHub Issues:** Report bugs and feature requests
- **Community:** Join discussions on GitHub

---

### Conclusion

The AI Codebase Onboarding Assistant is a powerful tool for understanding codebases, but it has limitations primarily around:
- Language support (Python and JavaScript only)
- Repository size and complexity
- LLM accuracy and rate limits
- Single-user deployment architecture

Understanding these limitations will help set appropriate expectations and guide effective usage of the system.

**For production deployments with critical requirements, consider:**
- Self-hosted LLM solutions
- Enhanced authentication and security
- Distributed vector store (Pinecone, Weaviate)
- Infrastructure scaling and monitoring
