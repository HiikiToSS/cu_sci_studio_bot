import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

export class MenuItem {
  static readonly STATISTICS = new MenuItem(
    "Статистика",
    <FontAwesomeIcon icon="fa-solid fa-chart-pie" />,
  );
  static readonly GRAPH = new MenuItem(
    "Граф",
    <FontAwesomeIcon icon="fa-solid fa-circle-nodes" />,
  );

  // private to disallow creating other instances of this type
  private constructor(
    private readonly key: string,
    public readonly icon: any,
  ) {}

  toString() {
    return this.key;
  }
}
