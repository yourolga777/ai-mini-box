export default function Help() {
  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Help</h1>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Installation</h2>
        <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
pip install ai-mini-box-core ai-mini-box-web{`\n`}pip install ai-mini-box-demo
        </pre>
        <p className="text-gray-600 text-sm">
          Or clone the repo and install in editable mode:
        </p>
        <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
git clone https://github.com/yourolga777/ai-mini-box.git{`\n`}cd ai-mini-box{`\n`}pip install -e packages/core/{`\n`}pip install -e packages/web/
        </pre>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Quick start</h2>
        <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
ai-mini-box init{`\n`}ai-mini-box serve
        </pre>
        <p className="text-gray-600 text-sm">
          Open <a href="http://127.0.0.1:8080" className="text-blue-600 underline">http://127.0.0.1:8080</a> in your browser.
        </p>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">One-click run</h2>
        <p className="text-gray-600 text-sm">
          Double-click <code className="bg-gray-100 px-1 rounded">run.bat</code> in the project root — it installs
          dependencies, initializes the project, and starts the server.
        </p>
        <p className="text-gray-600 text-sm">
          Double-click <code className="bg-gray-100 px-1 rounded">stop.bat</code> to stop the server.
        </p>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">CLI commands</h2>
        <div className="text-sm space-y-1 text-gray-700">
          <p><code className="bg-gray-100 px-1 rounded">ai-mini-box init</code> — create config and database</p>
          <p><code className="bg-gray-100 px-1 rounded">ai-mini-box check-db</code> — verify database connection</p>
          <p><code className="bg-gray-100 px-1 rounded">ai-mini-box db upgrade</code> — run pending migrations</p>
          <p><code className="bg-gray-100 px-1 rounded">ai-mini-box config show</code> — display configuration</p>
          <p><code className="bg-gray-100 px-1 rounded">ai-mini-box config set key value</code> — set a config value</p>
          <p><code className="bg-gray-100 px-1 rounded">ai-mini-box serve</code> — start web interface</p>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">API documentation</h2>
        <p className="text-gray-600 text-sm">
          Interactive Swagger UI is available at <a href="/docs" className="text-blue-600 underline">/docs</a> when the server is running.
        </p>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Links</h2>
        <div className="text-sm space-y-1">
          <p><a href="https://github.com/yourolga777/ai-mini-box" className="text-blue-600 underline" target="_blank" rel="noreferrer">GitHub</a></p>
          <p><a href="https://pypi.org/project/ai-mini-box-core/" className="text-blue-600 underline" target="_blank" rel="noreferrer">PyPI — ai-mini-box-core</a></p>
          <p><a href="https://pypi.org/project/ai-mini-box-web/" className="text-blue-600 underline" target="_blank" rel="noreferrer">PyPI — ai-mini-box-web</a></p>
        </div>
      </section>
    </div>
  );
}
