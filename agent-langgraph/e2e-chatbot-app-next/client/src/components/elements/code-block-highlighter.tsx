import { PrismAsyncLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import oneDark from 'react-syntax-highlighter/dist/esm/styles/prism/one-dark';
import oneLight from 'react-syntax-highlighter/dist/esm/styles/prism/one-light';

type CodeBlockHighlighterProps = {
  code: string;
  language: string;
  showLineNumbers?: boolean;
};

const highlighterStyle = {
  margin: 0,
  padding: '1rem',
  fontSize: '0.875rem',
  background: 'hsl(var(--background))',
  color: 'hsl(var(--foreground))',
  overflowX: 'auto',
  overflowWrap: 'break-word',
  wordBreak: 'break-all',
} as const;

const lineNumberStyle = {
  color: 'hsl(var(--muted-foreground))',
  paddingRight: '1rem',
  minWidth: '2.5rem',
};

const CodeBlockHighlighter = ({
  code,
  language,
  showLineNumbers = false,
}: CodeBlockHighlighterProps) => (
  <>
    <SyntaxHighlighter
      className="overflow-hidden dark:hidden"
      codeTagProps={{
        className: 'font-mono text-sm',
      }}
      customStyle={highlighterStyle}
      language={language}
      lineNumberStyle={lineNumberStyle}
      showLineNumbers={showLineNumbers}
      style={oneLight}
    >
      {code}
    </SyntaxHighlighter>
    <SyntaxHighlighter
      className="hidden overflow-hidden dark:block"
      codeTagProps={{
        className: 'font-mono text-sm',
      }}
      customStyle={highlighterStyle}
      language={language}
      lineNumberStyle={lineNumberStyle}
      showLineNumbers={showLineNumbers}
      style={oneDark}
    >
      {code}
    </SyntaxHighlighter>
  </>
);

export default CodeBlockHighlighter;
