import Statistic from "../components/Statistic";

export default function Statistics() {
  return (
    <div className="statistics">
      <Statistic name="Тебя указало" getValue={() => "100Чел."} />
    </div>
  );
}
