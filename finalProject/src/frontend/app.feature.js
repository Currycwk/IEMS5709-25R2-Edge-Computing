const BACKEND_ENDPOINTS = {
  local: 'http://localhost:8001',
  api: 'http://localhost:8100',
};
const { createApp } = Vue;

createApp({
  data() {
    const savedBackendTarget = window.localStorage.getItem('backendTarget');
    return {
      backendTarget: savedBackendTarget === 'api' ? 'api' : 'local',
      question: '', topK: 3, corpus: 'knowledge', codeProject: '', codeProjects: [],
      uploadProjectName: '', uploadFile: null, uploadBusy: false, deleteBusy: false, deleteKnowledgeBusy: false,
      knowledgeUploadFile: null, knowledgeUploadBusy: false,
      answerText: '等待提问...', answerStatus: '', thinkText: '', thinkExpanded: false,
      tokenBuffer: '', inThinkBlock: false, sourceNotice: '尚无检索结果。', sourceList: [],
      statusText: '等待检查', statusBusy: false, indexBusy: false, askBusy: false, docsBusy: false, streamBusy: false,
      documents: [], selectedDocumentPath: '', selectedDocument: null, docsCollapsed: true,
    };
  },
  computed: {
    currentBackendBase() { return BACKEND_ENDPOINTS[this.backendTarget] || BACKEND_ENDPOINTS.local; },
    backendTargetLabel() { return this.backendTarget === 'api' ? 'API 模型 (8100)' : '本地模型 (8001)'; },
    statusButtonLabel() { return this.statusBusy ? '检查中...' : '检查系统状态'; },
    indexButtonLabel() { return this.indexBusy ? '构建中...' : '构建索引'; },
    askButtonLabel() { return this.askBusy ? '生成中...' : '提交问题'; },
    docsButtonLabel() { return this.docsBusy ? '加载中...' : '刷新文档'; },
    uploadButtonLabel() { return this.uploadBusy ? '上传中...' : '上传并索引外部项目'; },
    knowledgeUploadButtonLabel() { return this.knowledgeUploadBusy ? '上传中...' : '上传知识库文件'; },
    deleteButtonLabel() { return this.deleteBusy ? '删除中...' : '删除当前项目'; },
    deleteKnowledgeButtonLabel() { return this.deleteKnowledgeBusy ? '删除中...' : '删除当前文件'; },
    thinkToggleLabel() { return this.thinkExpanded ? '收起 Think' : '展开 Think'; },
    hasThink() { return this.thinkText.trim().length > 0; },
    showCodeProjectSelector() { return this.corpus === 'external_code'; },
    showKnowledgeDeleteButton() { return this.corpus === 'knowledge' && !!this.selectedDocument?.path; },
    docsTitle() { return this.corpus === 'knowledge' ? 'Knowledge Base' : 'External Code Base'; },
    selectedPreview() { return this.selectedDocument ? (this.selectedDocument.content || this.selectedDocument.preview || '该文档暂无内容。') : '请选择文档。'; },
  },
  methods: {
    scrollAnswerToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.answerOutput;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
    async requestJson(path, options = {}) {
      const res = await fetch(`${this.currentBackendBase}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options });
      let data = {}; try { data = await res.json(); } catch (_) {}
      if (!res.ok) throw new Error(data.detail || data.message || `Request failed: ${res.status}`);
      return data;
    },
    resetResult() {
      this.answerText=''; this.answerStatus=''; this.thinkText=''; this.thinkExpanded=false;
      this.tokenBuffer=''; this.inThinkBlock=false; this.sourceNotice='尚无检索结果。'; this.sourceList=[];
      this.scrollAnswerToBottom();
    },
    consumeModelToken(fragment) {
      if (!fragment) return;
      const o = '<think>'; const c = '</think>'; this.tokenBuffer += fragment;
      while (this.tokenBuffer.length) {
        if (this.inThinkBlock) {
          const i = this.tokenBuffer.indexOf(c);
          if (i === -1) { const k = c.length - 1; if (this.tokenBuffer.length > k) { this.thinkText += this.tokenBuffer.slice(0, -k); this.tokenBuffer = this.tokenBuffer.slice(-k); } break; }
          this.thinkText += this.tokenBuffer.slice(0, i); this.tokenBuffer = this.tokenBuffer.slice(i + c.length); this.inThinkBlock = false; continue;
        }
        const i = this.tokenBuffer.indexOf(o);
        if (i === -1) { const k = o.length - 1; if (this.tokenBuffer.length > k) { this.answerText += this.tokenBuffer.slice(0, -k); this.tokenBuffer = this.tokenBuffer.slice(-k); this.scrollAnswerToBottom(); } break; }
        if (i > 0) { this.answerText += this.tokenBuffer.slice(0, i); this.scrollAnswerToBottom(); }
        this.tokenBuffer = this.tokenBuffer.slice(i + o.length); this.inThinkBlock = true;
      }
    },
    flushBuffer() {
      if (!this.tokenBuffer) return;
      if (this.inThinkBlock) this.thinkText += this.tokenBuffer; else this.answerText += this.tokenBuffer;
      this.tokenBuffer = '';
      this.scrollAnswerToBottom();
    },
    async loadCorporaMeta() {
      try {
        const result = await this.requestJson('/api/corpora');
        this.codeProjects = Array.isArray(result.external_code_projects) ? result.external_code_projects : [];
        if (!this.codeProjects.includes(this.codeProject)) this.codeProject = this.codeProjects[0] || '';
      } catch (_) { this.codeProjects = []; }
    },
    async loadDocuments() {
      this.docsBusy = true;
      try {
        const q = new URLSearchParams({ corpus: this.corpus });
        if (this.showCodeProjectSelector && this.codeProject) q.set('code_project', this.codeProject);
        const result = await this.requestJson(`/api/documents?${q.toString()}`);
        this.documents = Array.isArray(result.documents) ? result.documents : [];
        if (this.documents.length) {
          const hit = this.documents.find((d) => d.path === this.selectedDocumentPath) || this.documents[0];
          this.selectedDocumentPath = hit.path;
          this.selectedDocument = hit;
        } else { this.selectedDocumentPath=''; this.selectedDocument=null; }
      } catch (e) { this.answerText = `文档加载失败：${e.message}`; }
      finally { this.docsBusy = false; }
    },
    async checkStatus() {
      this.statusBusy = true; this.statusText = '检查中...';
      try {
        const s = await this.requestJson('/api/status');
        this.statusText = `target=${this.backendTarget} | backend=${s.backend} | index=${s.index_ready} | qwen=${s.qwen_ready} | corpus=${s.active_corpus || 'unknown'}`;
      } catch (e) { this.statusText = `状态检查失败：${e.message}`; }
      finally { this.statusBusy = false; }
    },
    async buildIndex() {
      this.indexBusy = true; this.answerText = '正在构建索引...';
      try {
        const payload = { corpus: this.corpus, code_project: this.showCodeProjectSelector ? this.codeProject : null };
        const r = await this.requestJson('/api/index', { method:'POST', body: JSON.stringify(payload) });
        this.answerText = `索引构建完成。corpus=${r.corpus}, docs=${r.documents}, chunks=${r.chunks}`;
        await this.loadDocuments();
      } catch (e) { this.answerText = `索引构建失败：${e.message}`; }
      finally { this.indexBusy = false; }
    },
    onKnowledgeUploadFileChange(event) { this.knowledgeUploadFile = event?.target?.files?.[0] || null; },
    onUploadFileChange(event) { this.uploadFile = event?.target?.files?.[0] || null; },
    async onBackendTargetChange() {
      window.localStorage.setItem('backendTarget', this.backendTarget);
      this.statusText = `已切换到${this.backendTargetLabel}`;
      this.codeProjects = [];
      this.codeProject = '';
      this.documents = [];
      this.selectedDocumentPath = '';
      this.selectedDocument = null;
      this.resetResult();
      await this.loadCorporaMeta();
      await this.loadDocuments();
    },
    async uploadKnowledgeDocument() {
      if (!this.knowledgeUploadFile) { this.answerText = '请先选择知识库文件。'; return; }

      this.knowledgeUploadBusy = true;
      try {
        const fd = new FormData();
        fd.append('file', this.knowledgeUploadFile);
        const res = await fetch(`${this.currentBackendBase}/api/knowledge/upload`, { method: 'POST', body: fd });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const message = data.detail || data.message || `Upload failed: ${res.status}`;
          if (res.status === 409) window.alert(`上传失败：${message}\n请先删除同名文件，或修改文件名后再上传。`);
          throw new Error(message);
        }

        this.answerText = `知识库文件上传完成：${data.filename}（docs=${data.documents}, chunks=${data.chunks}）`;
        this.corpus = 'knowledge';
        this.knowledgeUploadFile = null;
        await this.loadDocuments();
      } catch (e) { this.answerText = `上传失败：${e.message}`; }
      finally { this.knowledgeUploadBusy = false; }
    },
    async uploadExternalProject() {
      if (!this.uploadProjectName.trim()) { this.answerText = '请先输入项目名。'; return; }
      if (!this.uploadFile) { this.answerText = '请先选择 zip 文件。'; return; }
      this.uploadBusy = true;
      try {
        const fd = new FormData();
        fd.append('project_name', this.uploadProjectName.trim());
        fd.append('file', this.uploadFile);
        const res = await fetch(`${this.currentBackendBase}/api/code/upload`, { method: 'POST', body: fd });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || data.message || `Upload failed: ${res.status}`);

        this.answerText = `上传并索引完成：${data.project_name}（docs=${data.documents}, chunks=${data.chunks}）`;
        this.corpus = 'external_code';
        await this.loadCorporaMeta();
        this.codeProject = data.project_name;
        await this.loadDocuments();
      } catch (e) { this.answerText = `上传失败：${e.message}`; }
      finally { this.uploadBusy = false; }
    },
    async deleteExternalProject() {
      const projectName = this.codeProject.trim();
      if (!projectName) { this.answerText = '请先选择要删除的项目。'; return; }
      if (!window.confirm(`确认删除外部项目 ${projectName} 吗？`)) return;

      this.deleteBusy = true;
      try {
        const data = await this.requestJson(`/api/code/external/${encodeURIComponent(projectName)}`, { method: 'DELETE' });
        this.answerText = data.cleared_active_index
          ? `已删除项目 ${projectName}，并清空当前外部代码索引。`
          : `已删除项目 ${projectName}。`;
        await this.loadCorporaMeta();
        this.codeProject = this.codeProjects[0] || '';
        if (this.codeProject) {
          await this.loadDocuments();
        } else {
          this.documents = [];
          this.selectedDocumentPath = '';
          this.selectedDocument = null;
        }
      } catch (e) { this.answerText = `删除失败：${e.message}`; }
      finally { this.deleteBusy = false; }
    },
    async deleteKnowledgeDocument() {
      const docPath = this.selectedDocument?.path || '';
      const docName = this.selectedDocument?.source || '当前文件';
      if (!docPath) { this.answerText = '请先选择要删除的知识库文件。'; return; }
      if (!window.confirm(`确认删除知识库文件 ${docName} 吗？`)) return;

      this.deleteKnowledgeBusy = true;
      try {
        const data = await this.requestJson(`/api/knowledge/document?path=${encodeURIComponent(docPath)}`, { method: 'DELETE' });
        this.answerText = data.cleared_active_index
          ? `已删除知识库文件 ${docName}，并清空当前知识库索引。`
          : `已删除知识库文件 ${docName}。`;
        await this.loadDocuments();
      } catch (e) { this.answerText = `删除失败：${e.message}`; }
      finally { this.deleteKnowledgeBusy = false; }
    },
    async streamChat(question) {
      this.streamBusy = true;
      try {
        const payload = { question, top_k: this.topK, corpus: this.corpus, code_project: this.showCodeProjectSelector ? this.codeProject : null };
        const res = await fetch(`${this.currentBackendBase}/api/chat`, { method:'POST', headers:{ 'Content-Type':'application/json', Accept:'text/event-stream' }, body: JSON.stringify(payload) });
        if (!res.ok) throw new Error(await res.text());

        const reader = res.body.getReader(); const decoder = new TextDecoder('utf-8');
        let buffer = ''; let gotToken = false;
        this.answerText=''; this.answerStatus=''; this.sourceNotice='正在检索...'; this.sourceList=[];

        const consume = (chunk) => {
          const line = chunk.split('\n').find((x) => x.startsWith('data:')); if (!line) return;
          const raw = line.slice(5).trim(); if (!raw) return;
          let p; try { p = JSON.parse(raw); } catch (_) { return; }
          if (p.type === 'token') { gotToken = true; this.consumeModelToken(p.token || ''); }
          else if (p.type === 'warning') { this.answerStatus = p.message || '回答可能未完整'; }
          else if (p.type === 'sources') { this.sourceList = Array.isArray(p.sources) ? p.sources : []; this.sourceNotice = this.sourceList.length ? '' : '尚无检索结果。'; }
          else if (p.type === 'error') throw new Error(p.message || '流式失败');
          else if (p.type === 'done' && !this.answerStatus) this.answerStatus = '已完成';
        };

        while (true) {
          const { value, done } = await reader.read(); if (done) break;
          buffer += decoder.decode(value, { stream:true });
          const chunks = buffer.split('\n\n'); buffer = chunks.pop() || '';
          for (const c of chunks) consume(c);
        }
        buffer += decoder.decode(); if (buffer.trim()) consume(buffer);
        this.flushBuffer();
        if (!gotToken) throw new Error('未收到流式 token');
      } finally { this.streamBusy = false; }
    },
    async submitQuestion() {
      const q = this.question.trim(); if (!q) { this.answerText = '请输入问题。'; return; }
      this.askBusy = true; this.resetResult();
      try { await this.streamChat(q); this.question = ''; }
      catch (e) { this.answerText = `问答失败：${e.message}`; this.answerStatus = '请求失败'; }
      finally { this.askBusy = false; }
    },
    onCorpusChange() { this.loadDocuments(); },
    formatScore(v) { return (v === null || v === undefined || Number.isNaN(v)) ? 'n/a' : Number(v).toFixed(4); },
    pickDoc(doc) { this.selectedDocumentPath = doc.path; this.selectedDocument = doc; },
  },
  async mounted() { await this.loadCorporaMeta(); await this.loadDocuments(); },
  template: `<div><header class="hero"><p class="eyebrow">Vue 3 + LangChain + Qwen3 + BGE-M3</p><h1>Local RAG Console</h1><p class="subtitle">支持知识库问答与外部代码项目分析。</p><div class="status-row"><button type="button" @click="checkStatus" :disabled="statusBusy">{{ statusButtonLabel }}</button><button type="button" @click="loadDocuments" :disabled="docsBusy">{{ docsButtonLabel }}</button><span id="statusText">{{ statusText }}</span></div></header><main class="grid"><section class="panel question-panel"><h2>Ask</h2><label class="field-label">模型来源</label><select v-model="backendTarget" @change="onBackendTargetChange"><option value="local">本地模型（8001）</option><option value="api">API 模型（8100）</option></select><label class="field-label">语料模式</label><select v-model="corpus" @change="onCorpusChange"><option value="knowledge">知识库（data/raw）</option><option value="external_code">分析外部代码项目</option></select><div v-if="!showCodeProjectSelector" class="field-stack"><label class="field-label">上传知识库文件（支持 .txt / .md / .pdf）</label><input type="file" accept=".txt,.md,.pdf,application/pdf,text/plain,text/markdown" @change="onKnowledgeUploadFileChange" /><button type="button" @click="uploadKnowledgeDocument" :disabled="knowledgeUploadBusy">{{ knowledgeUploadButtonLabel }}</button></div><div v-if="showCodeProjectSelector" class="field-stack"><label class="field-label">外部项目</label><select v-model="codeProject" @change="loadDocuments"><option v-for="p in codeProjects" :key="p" :value="p">{{ p }}</option></select><div class="button-row"><button type="button" class="danger-btn" @click="deleteExternalProject" :disabled="deleteBusy || !codeProject">{{ deleteButtonLabel }}</button></div></div><div v-if="showCodeProjectSelector" class="field-stack"><label class="field-label">上传 ZIP 项目（自动解压并索引）</label><input type="text" v-model.trim="uploadProjectName" placeholder="项目名，例如 my_project" /><input type="file" accept=".zip" @change="onUploadFileChange" /><button type="button" @click="uploadExternalProject" :disabled="uploadBusy">{{ uploadButtonLabel }}</button></div><label class="field-label" for="topkRange">检索数量 Top-K：<strong>{{ topK }}</strong></label><input id="topkRange" v-model="topK" class="range-input" type="range" min="1" max="8" step="1" /><textarea v-model.trim="question" placeholder="例如：请分析这个项目后端架构与主要模块" @keydown.ctrl.enter.prevent="submitQuestion"></textarea><div class="button-row"><button type="button" @click="buildIndex" :disabled="indexBusy">{{ indexButtonLabel }}</button><button type="button" @click="submitQuestion" :disabled="askBusy || streamBusy">{{ askButtonLabel }}</button></div><p class="helper-text">当前连接：{{ backendTargetLabel }}。切换语料模式或外部项目后请先构建索引。</p></section><section class="panel answer-panel"><h2>Answer</h2><div v-if="hasThink" class="think-panel"><button type="button" class="think-toggle" @click="thinkExpanded=!thinkExpanded">{{ thinkToggleLabel }}</button><pre v-show="thinkExpanded" class="think-output">{{ thinkText }}</pre></div><pre ref="answerOutput" class="answer-output">{{ answerText || '等待提问...' }}</pre><p v-if="answerStatus" class="helper-text">{{ answerStatus }}</p></section><section class="panel docs-panel" :class="{ collapsed: docsCollapsed }"><div class="panel-heading"><h2>{{ docsTitle }}</h2><div class="button-row"><span class="helper-text">{{ documents.length }} 条</span><button v-if="showKnowledgeDeleteButton" type="button" class="danger-btn" @click="deleteKnowledgeDocument" :disabled="deleteKnowledgeBusy || !selectedDocument">{{ deleteKnowledgeButtonLabel }}</button><button type="button" class="collapse-btn" @click="docsCollapsed=!docsCollapsed">{{ docsCollapsed ? '展开' : '收起' }}</button></div></div><div v-show="!docsCollapsed" class="docs-layout"><div class="docs-list"><button v-for="d in documents" :key="d.path + '-' + (d.page || '')" type="button" class="doc-item" :class="{ active: selectedDocumentPath === d.path }" @click="pickDoc(d)"><span class="doc-name">{{ d.source }}</span><span class="doc-meta">{{ d.doc_type }} · {{ d.chars }} chars</span></button><div v-if="!documents.length" class="source-empty">当前模式暂无文档。</div></div><div class="doc-preview"><h3>{{ selectedDocument ? selectedDocument.source : '文档预览' }}</h3><pre class="doc-preview-content">{{ selectedPreview }}</pre></div></div></section><section class="panel source-panel"><h2>Sources</h2><div v-if="sourceList.length" class="source-list"><article v-for="s in sourceList" :key="s.source + '-' + formatScore(s.score)" class="source-card"><h3>{{ s.source }}</h3><div class="meta">score={{ formatScore(s.score) }} | corpus={{ s.corpus || 'unknown' }} | {{ s.language || s.doc_type || 'n/a' }}</div><div class="source-content">{{ s.content }}</div></article></div><div v-else class="source-empty">{{ sourceNotice }}</div></section></main></div>`,
}).mount('#app');
