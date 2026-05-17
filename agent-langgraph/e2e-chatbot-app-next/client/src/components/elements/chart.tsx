import type { ChartData, ChartSeries } from '@chat-template/core';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ComposedChart,
} from 'recharts';
import { cn } from '@/lib/utils';

const DEFAULT_COLORS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
];

type ChartPartProps = {
  chart: ChartData;
  className?: string;
};

const getSeriesColor = (series: ChartSeries, index: number) =>
  series.color ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length];

const renderBars = (series: ChartSeries[]) =>
  series.map((item, index) => (
    <Bar
      dataKey={item.key}
      fill={getSeriesColor(item, index)}
      key={item.key}
      name={item.label}
      radius={[4, 4, 0, 0]}
      yAxisId={item.yAxisId ?? 'left'}
    />
  ));

const renderLines = (series: ChartSeries[]) =>
  series.map((item, index) => (
    <Line
      activeDot={{ r: 5 }}
      dataKey={item.key}
      dot={{ r: 3 }}
      key={item.key}
      name={item.label}
      stroke={getSeriesColor(item, index)}
      strokeWidth={2.5}
      type="monotone"
      yAxisId={item.yAxisId ?? 'left'}
    />
  ));

export const ChartPart = ({ chart, className }: ChartPartProps) => {
  const barSeries = chart.series.filter((item) => item.kind !== 'line');
  const lineSeries = chart.series.filter((item) => item.kind === 'line');
  const hasRightAxis = chart.series.some((item) => item.yAxisId === 'right');

  if (!chart.data.length || !chart.series.length) {
    return (
      <section
        className={cn(
          'not-prose w-full rounded-xl border bg-card p-4 text-muted-foreground text-sm',
          className,
        )}
      >
        Chart data is unavailable.
      </section>
    );
  }

  return (
    <section
      className={cn('not-prose w-full rounded-xl border bg-card p-4', className)}
    >
      {(chart.title || chart.description) && (
        <div className="mb-3">
          {chart.title && (
            <h3 className="font-semibold text-base text-foreground">
              {chart.title}
            </h3>
          )}
          {chart.description && (
            <p className="mt-1 text-muted-foreground text-sm">
              {chart.description}
            </p>
          )}
        </div>
      )}

      <div className="h-80 w-full">
        <ResponsiveContainer height="100%" width="100%">
          {chart.kind === 'line' ? (
            <LineChart
              data={chart.data}
              margin={{ top: 16, right: 24, bottom: 8, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={chart.xKey} tickLine={false} />
              <YAxis tickLine={false} width={48} />
              <Tooltip />
              <Legend />
              {renderLines(chart.series)}
            </LineChart>
          ) : chart.kind === 'combo' ? (
            <ComposedChart
              data={chart.data}
              margin={{ top: 16, right: 24, bottom: 8, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={chart.xKey} tickLine={false} />
              <YAxis tickLine={false} width={48} yAxisId="left" />
              {hasRightAxis && (
                <YAxis
                  orientation="right"
                  tickLine={false}
                  width={48}
                  yAxisId="right"
                />
              )}
              <Tooltip />
              <Legend />
              {renderBars(barSeries)}
              {renderLines(lineSeries)}
            </ComposedChart>
          ) : (
            <BarChart
              data={chart.data}
              margin={{ top: 16, right: 24, bottom: 8, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={chart.xKey} tickLine={false} />
              <YAxis tickLine={false} width={48} />
              <Tooltip />
              <Legend />
              {renderBars(chart.series)}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </section>
  );
};
