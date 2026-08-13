// API service for communicating with FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class APIService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Health check
  async checkHealth() {
    return this.get('/health');
  }

  // RAG endpoints
  async ragIngest() {
    return this.post('/rag/ingest', {});
  }

  async ragQuery(query, topK = 20) {
    return this.post('/rag/query', { query, k: topK });
  }

  async ragQueryV2(query) {
    return this.post('/rag/query_v2', { query });
  }

  // Search endpoints (now proxy to RAG)
  async searchNetCDFData(query, topK = 20, useIndex = true) {
    const res = await this.ragQuery(query, topK);
    return {
      results: (res.results || []).map(r => ({
        file_path: r.file_path,
        score: r.score,
        source_netcdf: r.source_netcdf,
        parquet: r.parquet,
      })),
      method: 'faiss+parquet',
    };
  }

  async getSearchStatus() {
    return this.get('/search/status');
  }

  // Analysis endpoints
  async analyzeFiles(filePaths) {
    return this.post('/analyze', {
      file_paths: filePaths,
    });
  }

  async getMapData(filePaths) {
    return this.post('/map-data', {
      file_paths: filePaths,
    });
  }

  async generateInsights(query, fileStatistics) {
    return this.post('/insights', {
      query,
      file_statistics: fileStatistics,
    });
  }

  // Combined search and analysis workflow
  async searchAndAnalyze(query, topK = 20) {
    try {
      // 1. Try new V2 Hybrid API path
      try {
        const v2Res = await this.ragQueryV2(query);
        return {
          searchResults: { results: (v2Res.sources || []).map(s => ({ file_path: s, score: 1.0 })) },
          analysis: { file_statistics: v2Res.data || {} },
          mapData: { markers: [] },
          insights: { insights: v2Res.answer, answer: v2Res.answer, intent: v2Res.intent },
          error: null
        };
      } catch (e) {
        console.warn("V2 Query failed (possibly due to DB unavailability), falling back to legacy RAG.", e);
      }

      // 2. Legacy fallback
      const searchResults = await this.searchNetCDFData(query, topK);
      
      if (!searchResults.results || searchResults.results.length === 0) {
        return {
          searchResults,
          analysis: null,
          mapData: null,
          insights: null,
          error: 'No files found for the query',
        };
      }

      // Extract file paths from search results (prefer parquet)
      const filePaths = searchResults.results.map(result => result.file_path);

      // Analyze the files
      const analysis = await this.analyzeFiles(filePaths);
      
      // Get map data
      const mapData = await this.getMapData(filePaths);

      // Generate insights
      const insights = await this.generateInsights(query, analysis.file_statistics);

      return {
        searchResults,
        analysis,
        mapData,
        insights,
        error: null,
      };
    } catch (error) {
      return {
        searchResults: null,
        analysis: null,
        mapData: null,
        insights: null,
        error: error.message,
      };
    }
  }
}

export default new APIService();
