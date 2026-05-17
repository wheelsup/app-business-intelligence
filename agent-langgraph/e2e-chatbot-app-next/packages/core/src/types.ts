import { z } from 'zod';
import type { LanguageModelUsage, UIMessage } from 'ai';

const messageMetadataSchema = z.object({
  createdAt: z.string(),
});

type MessageMetadata = z.infer<typeof messageMetadataSchema>;

export type ChartKind = 'bar' | 'line' | 'combo';

export type ChartSeriesKind = 'bar' | 'line';

export interface ChartSeries {
  key: string;
  label: string;
  kind?: ChartSeriesKind;
  color?: string;
  yAxisId?: 'left' | 'right';
}

export interface ChartData {
  title?: string;
  description?: string;
  kind: ChartKind;
  xKey: string;
  data: Array<Record<string, string | number | null>>;
  series: ChartSeries[];
  xLabel?: string;
  yLabel?: string;
}

export type CustomUIDataTypes = {
  error: string;
  usage: LanguageModelUsage;
  traceId: string | null;
  title: string;
  chart: ChartData;
};

export type ChatMessage = UIMessage<MessageMetadata, CustomUIDataTypes>;
export type ChatTools = Record<string, never>;

export interface Attachment {
  name: string;
  url: string;
  contentType: string;
}

export type { VisibilityType } from '@chat-template/utils';

export interface Feedback {
  messageId: string;
  feedbackType: 'thumbs_up' | 'thumbs_down';
  assessmentId: string | null;
}

export type FeedbackMap = Record<string, Feedback>;
