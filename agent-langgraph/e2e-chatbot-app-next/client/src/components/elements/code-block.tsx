import { cn } from '@/lib/utils';
import type { HTMLAttributes, ReactNode } from 'react';
import { lazy, Suspense } from 'react';

const LazyCodeBlockHighlighter = lazy(() => import('./code-block-highlighter'));

type CodeBlockProps = HTMLAttributes<HTMLDivElement> & {
  code: string;
  language: string;
  showLineNumbers?: boolean;
  children?: ReactNode;
};

export const CodeBlock = ({
  code,
  language,
  showLineNumbers = false,
  className,
  children,
  ...props
}: CodeBlockProps) => (
  <div
    className={cn(
      'relative w-full overflow-hidden rounded-md border bg-background text-foreground',
      className,
    )}
    {...props}
  >
    <div className="relative">
      <Suspense
        fallback={
          <pre className="m-0 overflow-x-auto whitespace-pre-wrap break-all bg-background p-4 font-mono text-sm text-foreground">
            <code>{code}</code>
          </pre>
        }
      >
        <LazyCodeBlockHighlighter
          code={code}
          language={language}
          showLineNumbers={showLineNumbers}
        />
      </Suspense>
      {children && (
        <div className="absolute top-2 right-2 flex items-center gap-2">
          {children}
        </div>
      )}
    </div>
  </div>
);
