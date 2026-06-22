export default function Architecture() {
  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">Architecture</h1>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Overview</h2>
        <p className="text-gray-700 text-sm leading-relaxed">
          ai-mini-box is a modular monorepo for small business automation. It provides
          a layered Python core with domain models, infrastructure, CLI, and a
          plugin system — plus a web interface (PWA) built on FastAPI + React.
        </p>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-3">
        <h2 className="text-lg font-semibold">Project structure</h2>
        <pre className="bg-gray-100 p-3 rounded text-xs leading-relaxed overflow-x-auto">
ai-mini-box/
├── packages/
│   ├── core/              # Domain + infrastructure layer
│   │   └── ai_mini_box/
│   │       ├── core/          # Pydantic models, ABC repos, DI container
│   │       ├── infrastructure/ # SQLAlchemy ORM, config, logger, DB
│   │       ├── migrations/    # Alembic migrations (bundled)
│   │       └── cli.py         # Typer CLI + plugin loader
│   ├── web/               # FastAPI backend + React SPA
│   │   ├── ai_mini_box_web/
│   │   │   ├── routers/       # CRUD endpoints (contacts, products…)
│   │   │   ├── services/      # Plugin manager
│   │   │   ├── static/        # Built frontend assets
│   │   │   └── server.py      # FastAPI app factory
│   │   └── frontend/          # React + Vite + Tailwind + React Query
│   └── demo/              # Example plugin service
├── tool-*.md             # 30 service specifications
├── run.bat               # One-click run (Windows)
└── .github/workflows/    # CI + publish to PyPI
        </pre>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Layered architecture</h2>
        <div className="text-sm space-y-3">
          <div>
            <h3 className="font-medium text-gray-800">Core layer — packages/core/ai_mini_box/core/</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1 mt-1">
              <li><code className="bg-gray-100 px-1">models.py</code> — Pydantic v2 models: Contact, Product, Message, Order. Prices stored as integer kopecks.</li>
              <li><code className="bg-gray-100 px-1">repositories.py</code> — ABCs with QueryBuilder (method-chaining filter/search/sort/limit/offset).</li>
              <li><code className="bg-gray-100 px-1">container.py</code> — RepoContainer (DI) and AppContext (global singleton for CLI).</li>
              <li><code className="bg-gray-100 px-1">exceptions.py</code> — Custom domain exceptions.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-800">Infrastructure layer — packages/core/ai_mini_box/infrastructure/</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1 mt-1">
              <li><code className="bg-gray-100 px-1">database.py</code> — SQLAlchemy engine, <code>get_db()</code> context manager (auto-commit/rollback).</li>
              <li><code className="bg-gray-100 px-1">config.py</code> — JsonConfigManager with Fernet encryption for sensitive fields.</li>
              <li><code className="bg-gray-100 px-1">orm_models.py</code> — SQLAlchemy declarative models.</li>
              <li><code className="bg-gray-100 px-1">mapping.py</code> — Pydantic-to-ORM mapper.</li>
              <li><code className="bg-gray-100 px-1">logger.py</code> — Loguru setup with rotation (1 MB x 3 files).</li>
              <li><code className="bg-gray-100 px-1">repositories/</code> — SQLAlchemy implementations of ABC repos.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-800">Presentation layer</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1 mt-1">
              <li><strong>CLI:</strong> Typer app in <code>cli.py</code>, auto-loads plugins via entry points <code>ai_mini_box.tools</code>.</li>
              <li><strong>Web API:</strong> FastAPI with CRUD routers for contacts, products, messages, orders + Swagger UI at <code>/docs</code>.</li>
              <li><strong>Frontend:</strong> React 18 SPA with TypeScript, Vite, Tailwind CSS, React Query. Built into <code>static/</code>.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Plugin system</h2>
        <p className="text-gray-700 text-sm leading-relaxed">
          Any package can register CLI commands via the entry point group <code className="bg-gray-100 px-1">ai_mini_box.tools</code>.
          The web interface also discovers plugins at runtime and shows their status on the Plugins page.
        </p>
        <div className="text-sm text-gray-600">
          <p className="font-medium mt-2">To create a plugin:</p>
          <pre className="bg-gray-100 p-3 rounded text-xs mt-1 overflow-x-auto">
# pyproject.toml
[project.entry-points."ai_mini_box.tools"]
my_service = "my_package.commands:register"
          </pre>
          <p className="mt-2">The <code className="bg-gray-100 px-1">register(app)</code> function receives a Typer instance and adds subcommands.</p>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Tech stack</h2>
        <div className="text-sm grid grid-cols-2 gap-2 text-gray-700">
          <div className="bg-gray-50 p-2 rounded"><strong>Python</strong> ≥3.12</div>
          <div className="bg-gray-50 p-2 rounded"><strong>SQLAlchemy</strong> 2.0+</div>
          <div className="bg-gray-50 p-2 rounded"><strong>Pydantic</strong> v2</div>
          <div className="bg-gray-50 p-2 rounded"><strong>FastAPI</strong> + Uvicorn</div>
          <div className="bg-gray-50 p-2 rounded"><strong>React</strong> 18 + TypeScript</div>
          <div className="bg-gray-50 p-2 rounded"><strong>Vite</strong> + Tailwind</div>
          <div className="bg-gray-50 p-2 rounded"><strong>React Query</strong> (@tanstack)</div>
          <div className="bg-gray-50 p-2 rounded"><strong>SQLite</strong> (default DB)</div>
          <div className="bg-gray-50 p-2 rounded"><strong>Typer</strong> CLI</div>
          <div className="bg-gray-50 p-2 rounded"><strong>Alembic</strong> migrations</div>
          <div className="bg-gray-50 p-2 rounded"><strong>cryptography</strong> (Fernet)</div>
          <div className="bg-gray-50 p-2 rounded"><strong>loguru</strong> logging</div>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Key patterns</h2>
        <div className="text-sm space-y-2 text-gray-700">
          <div>
            <h3 className="font-medium">Repository pattern</h3>
            <p className="text-gray-600">Abstract base classes in <code className="bg-gray-100 px-1">core/</code>, SQLAlchemy implementations in <code className="bg-gray-100 px-1">infrastructure/repositories/</code>. Swap with mocks for testing.</p>
          </div>
          <div>
            <h3 className="font-medium">Dependency injection</h3>
            <p className="text-gray-600"><code className="bg-gray-100 px-1">RepoContainer(session)</code> — single entry point for all repos. Used via <code className="bg-gray-100 px-1">with get_db() as session: repos = RepoContainer(session)</code>.</p>
          </div>
          <div>
            <h3 className="font-medium">QueryBuilder</h3>
            <p className="text-gray-600">In-memory filtering on lists of Pydantic models. Supports <code className="bg-gray-100 px-1">.filter()</code>, <code className="bg-gray-100 px-1">.search()</code>, <code className="bg-gray-100 px-1">.sort()</code>, <code className="bg-gray-100 px-1">.limit()</code>, <code className="bg-gray-100 px-1">.offset()</code>.</p>
          </div>
          <div>
            <h3 className="font-medium">Migrations bundled</h3>
            <p className="text-gray-600">Alembic migrations live inside the installed package, not in a separate directory. <code className="bg-gray-100 px-1">ai-mini-box db upgrade</code> runs them programmatically.</p>
          </div>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Domain model</h2>
        <div className="text-sm text-gray-700">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b">
                <th className="py-1 pr-4">Entity</th>
                <th className="py-1 pr-4">Key fields</th>
                <th className="py-1">Relations</th>
              </tr>
            </thead>
            <tbody className="text-gray-600">
              <tr className="border-b">
                <td className="py-1 pr-4 font-medium">Contact</td>
                <td className="py-1 pr-4">name, phone, email, telegram_id</td>
                <td className="py-1">has messages, has orders</td>
              </tr>
              <tr className="border-b">
                <td className="py-1 pr-4 font-medium">Product</td>
                <td className="py-1 pr-4">name, price (kopecks)</td>
                <td className="py-1">—</td>
              </tr>
              <tr className="border-b">
                <td className="py-1 pr-4 font-medium">Message</td>
                <td className="py-1 pr-4">content, source (telegram/email/…), topic</td>
                <td className="py-1">belongs to Contact</td>
              </tr>
              <tr>
                <td className="py-1 pr-4 font-medium">Order</td>
                <td className="py-1 pr-4">status, items, total</td>
                <td className="py-1">belongs to Contact</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Testing</h2>
        <div className="text-sm text-gray-700 space-y-1">
          <p><strong>96 tests total</strong> (74 core + 13 web + 9 demo)</p>
          <ul className="list-disc list-inside text-gray-600 space-y-1 mt-1">
            <li>Core: unit tests (config, logger) + integration (CLI commands, repos, DB)</li>
            <li>Web: API endpoints via FastAPI TestClient with tmp_path DB</li>
            <li>Demo: E2E with CliRunner</li>
            <li>All use in-memory or temp-file SQLite</li>
          </ul>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow-sm space-y-2">
        <h2 className="text-lg font-semibold">Service specifications</h2>
        <p className="text-gray-700 text-sm">
          The repo includes 30+ <code className="bg-gray-100 px-1">tool-*.md</code> files with detailed specs for services:
          Telegram bot, Email, WhatsApp, SMS, CRM sync, Invoices, Calendar, AI lawyer, and more.
          Each spec describes commands, data model, and integration points.
        </p>
      </section>
    </div>
  );
}
