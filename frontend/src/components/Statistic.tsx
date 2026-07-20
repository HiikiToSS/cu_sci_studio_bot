interface StatisticProps {
  name: string;
  getValue: () => string;
}

export default function Statistic({ name, getValue }: StatisticProps) {
  return (
    <div className="statistic">
      <span className="statistic-name">{name}</span>
      <span className="statistic-value">{getValue()}</span>
    </div>
  );
}
