import CodeBlockLowlight from "@tiptap/extension-code-block-lowlight";
import { NodeViewContent, NodeViewWrapper, ReactNodeViewRenderer, type ReactNodeViewProps } from "@tiptap/react";
import { common, createLowlight } from "lowlight";

const lowlight = createLowlight(common);

const LANGUAGES: [string, string][] = [
  ["", "Auto-detect"], ["plaintext", "Plain text"], ["bash", "Bash"], ["c", "C"], ["cpp", "C++"], ["csharp", "C#"],
  ["css", "CSS"], ["go", "Go"], ["xml", "HTML / XML"], ["java", "Java"], ["javascript", "JavaScript"], ["json", "JSON"],
  ["kotlin", "Kotlin"], ["markdown", "Markdown"], ["php", "PHP"], ["python", "Python"], ["ruby", "Ruby"], ["rust", "Rust"],
  ["sql", "SQL"], ["swift", "Swift"], ["typescript", "TypeScript"], ["yaml", "YAML"],
];

function CodeBlockView({ node, updateAttributes, editor }: ReactNodeViewProps) {
  return (
    <NodeViewWrapper className="code-block">
      <select
        className="code-language"
        contentEditable={false}
        disabled={!editor.isEditable}
        value={node.attrs.language ?? ""}
        onChange={(e) => updateAttributes({ language: e.target.value || null })}
        aria-label="Code language"
      >
        {LANGUAGES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>
      <pre>
        <NodeViewContent<"code"> as="code" />
      </pre>
    </NodeViewWrapper>
  );
}

/** Code block with syntax colours and a language picker. Same node name and JSON as the
 * plain StarterKit code block, so older notes keep working. */
export const CodeBlock = CodeBlockLowlight.extend({
  addNodeView() {
    return ReactNodeViewRenderer(CodeBlockView);
  },
}).configure({ lowlight, defaultLanguage: null });
