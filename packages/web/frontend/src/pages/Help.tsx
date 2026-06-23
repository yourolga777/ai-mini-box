import { useQuery } from "@tanstack/react-query";

function mdToHtml(text: string): string {
  const lines = text.split("\n");
  let html = "";
  let inCode = false;
  let inTable = false;

  for (const raw of lines) {
    const line = raw.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    if (line.startsWith("```")) {
      if (inCode) { html += "</pre>\n"; inCode = false; }
      else { html += '<pre class="bg-gray-900 text-green-300 text-xs p-3 rounded overflow-x-auto my-2">\n'; inCode = true; }
      continue;
    }
    if (inCode) { html += line + "\n"; continue; }

    if (line.startsWith("# ")) {
      html += `<h2 class="text-lg font-bold mt-4 mb-2">${linkify(escapeBold(line.slice(2)))}</h2>\n`;
      continue;
    }
    if (line.startsWith("## ")) {
      html += `<h3 class="text-base font-semibold mt-3 mb-1">${linkify(escapeBold(line.slice(3)))}</h3>\n`;
      continue;
    }

    if (line.startsWith("|") && line.endsWith("|")) {
      if (!inTable) {
        inTable = true;
        html += '<table class="w-full text-left text-sm my-2 border-collapse"><thead><tr class="border-b">';
        for (const cell of line.split("|").filter(Boolean)) {
          html += `<th class="py-1 pr-4 font-medium">${cell.trim()}</th>`;
        }
        html += "</tr></thead><tbody>\n";
      } else if (line.includes("---")) {
        continue;
      } else {
        html += "<tr class=\"border-b\">";
        for (const cell of line.split("|").filter(Boolean)) {
          html += `<td class="py-1 pr-4 text-gray-600">${cell.trim()}</td>`;
        }
        html += "</tr>\n";
      }
      continue;
    }
    if (inTable && !line.startsWith("|")) {
      html += "</tbody></table>\n";
      inTable = false;
    }

    if (line.startsWith("- ")) {
      html += `<li class="text-gray-600 ml-4 list-disc">${inline(line.slice(2))}</li>\n`;
      continue;
    }

    if (line.trim() === "") {
      if (inTable) { html += "</tbody></table>\n"; inTable = false; }
      continue;
    }

    const rendered = inline(line);
    if (rendered) {
      html += `<p class="text-gray-700 text-sm my-1">${rendered}</p>\n`;
    }
  }

  if (inCode) html += "</pre>\n";
  if (inTable) html += "</tbody></table>\n";
  return html;
}

function escapeBold(t: string): string {
  return t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function linkify(t: string): string {
  return t.replace(
    /https?:\/\/[^\s<]+/g,
    (url) => `<a href="${url}" class="text-blue-600 underline" target="_blank" rel="noreferrer">${url}</a>`
  );
}

function inline(t: string): string {
  let s = t
    .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded text-xs">$1</code>')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/https?:\/\/[^\s<]+/g,
    (url) => `<a href="${url}" class="text-blue-600 underline" target="_blank" rel="noreferrer">${url}</a>`
  );
  return s;
}

interface Section {
  id: string;
  title: string;
  content: string;
  source: string;
  order: number;
}

export default function Help() {
  const { data, isLoading } = useQuery<Section[]>({
    queryKey: ["help"],
    queryFn: () => fetch("/api/help").then((r) => r.json()),
  });

  if (isLoading) return <p className="text-gray-500">Loading help...</p>;

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-6">Help</h1>

      <div className="flex gap-8">
        <nav className="w-48 shrink-0 space-y-1 sticky top-4 self-start">
          <p className="text-xs text-gray-400 uppercase mb-2">Sections</p>
          {(data ?? []).map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="block text-sm text-gray-600 hover:text-blue-600 transition"
            >
              {s.title}
            </a>
          ))}
        </nav>

        <div className="flex-1 space-y-6">
          {(data ?? []).map((s) => (
            <section key={s.id} id={s.id} className="bg-white p-4 rounded shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-bold">{s.title}</h2>
                <span className="text-xs text-gray-400">{s.source}</span>
              </div>
              <div dangerouslySetInnerHTML={{ __html: mdToHtml(s.content) }} />
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
