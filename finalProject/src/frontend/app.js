const backendBase = window.location.origin.includes('9898') ? 'http://localhost:8001' : '';

const { createApp } = Vue;

createApp({
  data() {
    return {
      question: '',
      answerText: '等待提问...',
      answerStatus: '',
      answerPlaceholder: '等待提问...',
      thinkText: '',
      thinkExpanded: false,
      tokenBuffer: '',
      inThinkBlock: false,
      sourceNotice: '尚无检索结果。',
      sourceList: [],
      statusText: '等待检查',
      statusReady: false,
      statusBusy: false,
      indexBusy: false,
      askBusy: false,
      streamBusy: false,
      activeRequestId: 0,
    };
  },
  computed: {
    isBusy() {
      return this.statusBusy || this.indexBusy || this.askBusy || this.streamBusy;
    },
    statusButtonLabel() {
      return this.statusBusy ? '检查中...' : '检查系统状态';
    },
    indexButtonLabel() {
      return this.indexBusy ? '构建中...' : '构建索引';
    },
    askButtonLabel() {
      return this.askBusy ? '生成中...' : '提交问题';
    },
    answerLabel() {
      return this.answerText;
    },
    answerStatusLabel() {
      return this.answerStatus;
    },
    hasThink() {
      return this.thinkText.trim().length > 0;
    },
    thinkToggleLabel() {
      return this.thinkExpanded ? '收起 Think' : '展开 Think';
    },
  },
  methods: {
    resetResult() {
      this.answerText = '';
      this.answerStatus = '';
      this.thinkText = '';
      this.thinkExpanded = false;
      this.tokenBuffer = '';
      this.inThinkBlock = false;
      this.sourceNotice = '尚无检索结果。';
      this.sourceList = [];
    },
    appendAnswer(text) {
      if (!text) {
        return;
      }
      this.answerText += text;
    },
    appendThink(text) {
      if (!text) {
        return;
      }
      this.thinkText += text;
    },
    consumeModelToken(fragment) {
      if (!fragment) {
        return;
      }

      const openTag = '<think>';
      const closeTag = '</think>';
      this.tokenBuffer += fragment;

      while (this.tokenBuffer.length > 0) {
        if (this.inThinkBlock) {
          const closeIndex = this.tokenBuffer.indexOf(closeTag);
          if (closeIndex === -1) {
            const keepTail = closeTag.length - 1;
            if (this.tokenBuffer.length > keepTail) {
              this.appendThink(this.tokenBuffer.slice(0, -keepTail));
              this.tokenBuffer = this.tokenBuffer.slice(-keepTail);
            }
            break;
          }

          this.appendThink(this.tokenBuffer.slice(0, closeIndex));
          this.tokenBuffer = this.tokenBuffer.slice(closeIndex + closeTag.length);
          this.inThinkBlock = false;
          continue;
        }

        const openIndex = this.tokenBuffer.indexOf(openTag);
        if (openIndex === -1) {
          const keepTail = openTag.length - 1;
          if (this.tokenBuffer.length > keepTail) {
            this.appendAnswer(this.tokenBuffer.slice(0, -keepTail));
            this.tokenBuffer = this.tokenBuffer.slice(-keepTail);
          }
          break;
        }

        if (openIndex > 0) {
          this.appendAnswer(this.tokenBuffer.slice(0, openIndex));
        }

        this.tokenBuffer = this.tokenBuffer.slice(openIndex + openTag.length);
        this.inThinkBlock = true;
      }
    },
    flushModelTokenBuffer() {
      if (!this.tokenBuffer) {
        return;
      }

      if (this.inThinkBlock) {
        this.appendThink(this.tokenBuffer);
      } else {
        this.appendAnswer(this.tokenBuffer);
      }

      this.tokenBuffer = '';
    },
    toggleThink() {
      this.thinkExpanded = !this.thinkExpanded;
    },
    startRequest() {
      this.activeRequestId += 1;
      return this.activeRequestId;
    },
    isCurrentRequest(requestId) {
      return requestId === this.activeRequestId;
    },
    async requestJson(path, options = {}) {
      const response = await fetch(`${backendBase}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      let data = {};
      try {
        data = await response.json();
      } catch (_) {
        data = {};
      }
      if (!response.ok) {
        throw new Error(data.detail || data.message || `Request failed with status ${response.status}`);
      }
      return data;
    },
    async streamChat(question) {
      const requestId = this.startRequest();
      this.streamBusy = true;
      try {
        const response = await fetch(`${backendBase}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
          },
          cache: 'no-store',
          body: JSON.stringify({ question }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || `Request failed with status ${response.status}`);
        }

        if (!response.body) {
          throw new Error('Streaming is not supported in this browser');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let receivedToken = false;
        let receivedDone = false;

        this.answerText = '';
        this.answerStatus = '';
        this.sourceNotice = '正在检索...';
        this.sourceList = [];

        const consumeChunk = (chunk) => {
          const dataLine = chunk
            .split('\n')
            .find((line) => line.startsWith('data:'));
          if (!dataLine) {
            return;
          }

          const payloadText = dataLine.slice(5).trim();
          if (!payloadText) {
            return;
          }

          let payload;
          try {
            payload = JSON.parse(payloadText);
          } catch (_) {
            return;
          }

          if (payload.type === 'start') {
            return;
          }

          if (payload.type === 'token') {
            receivedToken = true;
            this.consumeModelToken(payload.token || '');
          } else if (payload.type === 'sources') {
            this.sourceList = Array.isArray(payload.sources) ? payload.sources : [];
            this.sourceNotice = this.sourceList.length ? '' : '尚无检索结果。';
          } else if (payload.type === 'error') {
            throw new Error(payload.message || '流式响应失败');
          } else if (payload.type === 'done') {
            receivedDone = true;
            this.answerStatus = '已完成';
            return;
          }
        };

        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const chunks = buffer.split('\n\n');
          buffer = chunks.pop() || '';

          if (!this.isCurrentRequest(requestId)) {
            break;
          }

          for (const chunk of chunks) {
            consumeChunk(chunk);
          }
        }

        buffer += decoder.decode();
        if (buffer.trim()) {
          consumeChunk(buffer);
        }

        this.flushModelTokenBuffer();

        if (!receivedToken) {
          throw new Error('未收到流式 token');
        }

        if (!this.answerText.trim() && this.hasThink) {
          this.answerText = '模型仅返回了思考过程，请展开 Think 查看。';
        }

        this.answerStatus = '已完成';
      } finally {
        this.streamBusy = false;
      }
    },
    async checkStatus() {
      this.statusBusy = true;
      this.statusText = '检查中...';
      try {
        const status = await this.requestJson('/api/status');
        this.statusReady = true;
        this.statusText = `backend=${status.backend} | index=${status.index_ready} | qwen=${status.qwen_ready}`;
      } catch (error) {
        this.statusReady = false;
        this.statusText = `状态检查失败：${error.message}`;
      } finally {
        this.statusBusy = false;
      }
    },
    async buildIndex() {
      this.indexBusy = true;
      this.answerText = '正在构建索引...';
      try {
        const result = await this.requestJson('/api/index', { method: 'POST', body: '{}' });
        this.answerText = `索引构建完成。documents=${result.documents}, chunks=${result.chunks}`;
      } catch (error) {
        this.answerText = `索引构建失败：${error.message}`;
      } finally {
        this.indexBusy = false;
      }
    },
    async submitQuestion() {
      const question = this.question.trim();
      if (!question) {
        this.answerText = '请输入问题。';
        return;
      }

      this.askBusy = true;
      this.resetResult();
      this.sourceNotice = '正在检索...';
      this.sourceList = [];
      this.question = '';

      try {
        await this.streamChat(question);
      } catch (error) {
        this.answerText = `问答失败：${error.message || '流式请求失败'}`;
        this.answerStatus = '请求失败';
        this.sourceNotice = '无可展示的来源。';
        this.sourceList = [];
      } finally {
        this.askBusy = false;
      }
    },
    formatScore(score) {
      if (score === null || score === undefined || Number.isNaN(score)) {
        return 'n/a';
      }
      return Number(score).toFixed(4);
    },
  },
  template: `
    <div>
      <header class="hero">
        <p class="eyebrow">Vue 3 + LangChain + Qwen3 + BGE-M3</p>
        <h1>Local RAG Console</h1>
        <p class="subtitle">在本地知识库上进行检索增强问答，查看答案与检索来源。</p>
        <div class="status-row">
          <button type="button" @click="checkStatus" :disabled="statusBusy">{{ statusButtonLabel }}</button>
          <span id="statusText">{{ statusText }}</span>
        </div>
      </header>

      <main class="grid">
        <section class="panel question-panel">
          <h2>Ask</h2>
          <textarea
            v-model.trim="question"
            placeholder="请输入你的问题，例如：什么是 RAG？"
            @keydown.ctrl.enter.prevent="submitQuestion"
          ></textarea>
          <div class="button-row">
            <button type="button" @click="buildIndex" :disabled="indexBusy">{{ indexButtonLabel }}</button>
            <button type="button" @click="submitQuestion" :disabled="askBusy || streamBusy">{{ askButtonLabel }}</button>
          </div>
          <p class="helper-text">按 <strong>Ctrl</strong> + <strong>Enter</strong> 可以直接提交问题。</p>
        </section>

        <section class="panel answer-panel">
          <h2>Answer</h2>
          <div v-if="hasThink" class="think-panel">
            <button type="button" class="think-toggle" @click="toggleThink">{{ thinkToggleLabel }}</button>
            <pre v-show="thinkExpanded" class="think-output">{{ thinkText }}</pre>
          </div>
          <pre class="answer-output">{{ answerLabel }}</pre>
          <p v-if="answerStatusLabel" class="helper-text">{{ answerStatusLabel }}</p>
        </section>

        <section class="panel source-panel">
          <h2>Sources</h2>
          <div v-if="sourceList.length" class="source-list">
            <article v-for="source in sourceList" :key="source.source + '-' + formatScore(source.score)" class="source-card">
              <h3>{{ source.source }}</h3>
              <div class="meta">相似度分数：{{ formatScore(source.score) }}</div>
              <div class="source-content">{{ source.content }}</div>
            </article>
          </div>
          <div v-else class="source-empty">{{ sourceNotice }}</div>
        </section>
      </main>
    </div>
  `,
}).mount('#app');
