import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

interface SalesSummary {
  revenue: number;
  purchases: number;
  customers: number;
  courses: number;
  average_check: number;
  repeat_customers: number;
  repeat_rate: number;
}

interface Course {
  course: string;
  purchases: number;
  customers: number;
  revenue: number;
  average_check: number;
}

interface DailySale {
  date: string;
  purchases: number;
  revenue: number;
}

interface Funnel {
  clicks: number;
  bot_starts: number;
  leads: number;
  buyers: number;
  revenue: number;
}

interface Attribution {
  campaign_id: string;
  campaign_name: string;
  placement_id: string;
  channel_name: string;
  creative_id: string;
  cost: number;
  touches: number;
  leads: number;
  buyers: number;
  revenue: number;
  romi: number;
}

interface StudentTouch {
  touch_id: number;
  campaign_id: string;
  placement_id: string;
  creative_id: string;
  tracking_id: string;
  event_type: string;
  touched_at: string;
}

interface StudentPurchase {
  sale_id: number;
  course: string;
  amount: number;
  purchased_at: string;
}

interface StudentJourney {
  student_id: string;
  touches: StudentTouch[];
  purchases: StudentPurchase[];
  total_revenue: number;
}

const money = (value: number) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(value);

const number = (value: number) =>
  new Intl.NumberFormat("ru-RU").format(value);

const percent = (value: number) => `${value.toFixed(1)}%`;

function App() {
  const [sales, setSales] = useState<SalesSummary | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [daily, setDaily] = useState<DailySale[]>([]);
  const [funnel, setFunnel] = useState<Funnel | null>(null);
  const [attribution, setAttribution] = useState<Attribution[]>([]);

  const [studentId, setStudentId] = useState("");
  const [journey, setJourney] = useState<StudentJourney | null>(null);
  const [journeyError, setJourneyError] = useState("");

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [
          salesResponse,
          coursesResponse,
          dailyResponse,
          funnelResponse,
          attributionResponse,
        ] = await Promise.all([
          fetch(`${API_URL}/analytics/sales`),
          fetch(`${API_URL}/analytics/sales/courses`),
          fetch(`${API_URL}/analytics/sales/daily`),
          fetch(`${API_URL}/analytics/funnel`),
          fetch(`${API_URL}/analytics/attribution`),
        ]);

        const [
          salesData,
          coursesData,
          dailyData,
          funnelData,
          attributionData,
        ] = await Promise.all([
          salesResponse.json(),
          coursesResponse.json(),
          dailyResponse.json(),
          funnelResponse.json(),
          attributionResponse.json(),
        ]);

        setSales(salesData);
        setCourses(coursesData);
        setDaily(dailyData);
        setFunnel(funnelData);
        setAttribution(attributionData);
      } catch (error) {
        console.error("Ошибка загрузки данных:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  async function searchStudent() {
    if (!studentId.trim()) return;

    setJourneyError("");
    setJourney(null);

    try {
      const response = await fetch(
        `${API_URL}/analytics/attribution/${studentId.trim()}`
      );

      if (!response.ok) {
        throw new Error();
      }

      const data = await response.json();

      if (
        data.touches.length === 0 &&
        data.purchases.length === 0
      ) {
        setJourneyError("Пользователь не найден");
        return;
      }

      setJourney(data);
    } catch {
      setJourneyError("Не удалось найти пользователя");
    }
  }

  if (loading) {
    return <div className="loading">Загрузка аналитики...</div>;
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <p>
            Анализ продаж и эффективности маркетинговых активностей
          </p>
        </div>

        <div className="status">
          <span className="status-dot" />
          System online
        </div>
      </header>

      <main>
        {/* REAL SALES */}

        <section className="section">
          <div className="section-title">
            <div>
              <h2>Реальные продажи</h2>
              <p>Данные из исходного файла base.xlsx</p>
            </div>

            <span className="badge real">REAL DATA</span>
          </div>

          <div className="kpi-grid">
            <Kpi
              title="Выручка"
              value={money(sales?.revenue ?? 0)}
            />

            <Kpi
              title="Покупки"
              value={number(sales?.purchases ?? 0)}
            />

            <Kpi
              title="Покупатели"
              value={number(sales?.customers ?? 0)}
            />

            <Kpi
              title="Продукты"
              value={number(sales?.courses ?? 0)}
            />

            <Kpi
              title="Средний чек"
              value={money(sales?.average_check ?? 0)}
            />

            <Kpi
              title="Повторные покупки"
              value={percent(sales?.repeat_rate ?? 0)}
            />
          </div>

          <div className="grid two-columns">
            <Card title="Выручка по дням">
              <div className="chart">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={daily}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) =>
                        value.slice(5)
                      }
                    />
                    <YAxis />
                    <Tooltip
                      formatter={(value) => [
                        money(Number(value)),
                        "Выручка",
                      ]}
                    />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      strokeWidth={3}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title="Продажи по продуктам">
              <div className="chart">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={courses.slice(0, 8)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="course"
                      tick={false}
                    />
                    <YAxis />
                    <Tooltip
                      formatter={(value) => [
                        money(Number(value)),
                        "Выручка",
                      ]}
                    />
                    <Bar
                      dataKey="revenue"
                      name="Выручка"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          <Card title="Продукты">
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Курс</th>
                    <th>Покупки</th>
                    <th>Покупатели</th>
                    <th>Выручка</th>
                    <th>Средний чек</th>
                  </tr>
                </thead>

                <tbody>
                  {courses.map((course) => (
                    <tr key={course.course}>
                      <td className="main-cell">
                        {course.course}
                      </td>
                      <td>{number(course.purchases)}</td>
                      <td>{number(course.customers)}</td>
                      <td>{money(course.revenue)}</td>
                      <td>{money(course.average_check)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </section>

        {/* MARKETING */}

        <section className="section">
          <div className="section-title">
            <div>
              <h2>Маркетинговая эффективность</h2>
              <p>
                Связка рекламного касания с реальными покупками
              </p>
            </div>

            <span className="badge synthetic">
              SYNTHETIC MARKETING DATA
            </span>
          </div>

          <div className="notice">
            <strong>Важно:</strong> рекламные расходы и касания
            синтетические, так как исторические данные о рекламе
            отсутствуют. Выручка при этом берётся из реальных продаж.
            ROMI ниже — демонстрационный.
          </div>

          <div className="grid two-columns">
            <Card title="Воронка">
              <div className="funnel">
                <FunnelStep
                  title="Клики"
                  value={funnel?.clicks ?? 0}
                />

                <FunnelArrow />

                <FunnelStep
                  title="Запуски бота"
                  value={funnel?.bot_starts ?? 0}
                />

                <FunnelArrow />

                <FunnelStep
                  title="Лиды"
                  value={funnel?.leads ?? 0}
                />

                <FunnelArrow />

                <FunnelStep
                  title="Покупатели"
                  value={funnel?.buyers ?? 0}
                />

                <FunnelArrow />

                <FunnelStep
                  title="Выручка"
                  value={money(funnel?.revenue ?? 0)}
                />
              </div>
            </Card>

            <Card title="Ключевые выводы">
              <div className="insights">
                <Insight
                  title="Главная метрика"
                  text="Для оценки рекламы используем ROMI: (выручка − расходы) / расходы."
                />

                <Insight
                  title="Атрибуция"
                  text="Каждая покупка связывается с последним рекламным касанием пользователя."
                />

                <Insight
                  title="Источник истины"
                  text="Выручка и покупки берутся только из реального слоя продаж."
                />

                <Insight
                  title="Следующий шаг"
                  text="В продакшене синтетические касания заменяются реальными Telegram tracking-ссылками."
                />
              </div>
            </Card>
          </div>

          <Card title="Эффективность рекламных размещений">
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Кампания</th>
                    <th>Канал</th>
                    <th>Расход</th>
                    <th>Лиды</th>
                    <th>Покупатели</th>
                    <th>Выручка</th>
                    <th>ROMI</th>
                  </tr>
                </thead>

                <tbody>
                  {attribution.map((item) => (
                    <tr key={item.placement_id}>
                      <td className="main-cell">
                        {item.campaign_name}
                      </td>

                      <td>{item.channel_name}</td>

                      <td>{money(item.cost)}</td>

                      <td>{number(item.leads)}</td>

                      <td>{number(item.buyers)}</td>

                      <td>{money(item.revenue)}</td>

                      <td>
                        <span
                          className={
                            item.romi >= 0
                              ? "romi positive"
                              : "romi negative"
                          }
                        >
                          {percent(item.romi)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </section>

        {/* CUSTOMER JOURNEY */}

        <section className="section">
          <div className="section-title">
            <div>
              <h2>Customer Journey</h2>
              <p>
                Путь пользователя от рекламного касания до покупки
              </p>
            </div>

            <span className="badge">ATTRIBUTION</span>
          </div>

          <Card title="Поиск пользователя">
            <div className="search-row">
              <input
                value={studentId}
                onChange={(event) =>
                  setStudentId(event.target.value)
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    searchStudent();
                  }
                }}
                placeholder="Введите student_id"
              />

              <button onClick={searchStudent}>
                Найти
              </button>
            </div>

            {journeyError && (
              <div className="error">
                {journeyError}
              </div>
            )}
          </Card>

          {journey && (
            <Card
              title={`Пользователь ${journey.student_id}`}
            >
              <div className="journey-summary">
                <div>
                  <span>Реальная выручка</span>
                  <strong>
                    {money(journey.total_revenue)}
                  </strong>
                </div>

                <div>
                  <span>Касаний</span>
                  <strong>
                    {journey.touches.length}
                  </strong>
                </div>

                <div>
                  <span>Покупок</span>
                  <strong>
                    {journey.purchases.length}
                  </strong>
                </div>
              </div>

              <div className="journey">
                {journey.touches.map((touch, index) => (
                  <div
                    className="journey-item"
                    key={`${touch.touch_id}-${index}`}
                  >
                    <div className="journey-dot synthetic-dot">
                      🟡
                    </div>

                    <div>
                      <strong>
                        {formatEvent(touch.event_type)}
                      </strong>

                      <p>
                        {touch.placement_id}
                      </p>

                      <small>
                        {formatDate(touch.touched_at)}
                      </small>
                    </div>
                  </div>
                ))}

                {journey.purchases.map((purchase) => (
                  <div
                    className="journey-item"
                    key={purchase.sale_id}
                  >
                    <div className="journey-dot real-dot">
                      🟢
                    </div>

                    <div>
                      <strong>
                        Покупка — {purchase.course}
                      </strong>

                      <p>
                        {money(purchase.amount)}
                      </p>

                      <small>
                        {formatDate(
                          purchase.purchased_at
                        )}
                      </small>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </section>
      </main>

      <footer>
        Marketing Analytics MVP · Real Sales + Synthetic Marketing Measurement
      </footer>
    </div>
  );
}

function Kpi({
  title,
  value,
}: {
  title: string;
  value: string;
}) {
  return (
    <div className="kpi">
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function FunnelStep({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) {
  return (
    <div className="funnel-step">
      <span>{title}</span>
      <strong>{typeof value === "number" ? number(value) : value}</strong>
    </div>
  );
}

function FunnelArrow() {
  return <div className="funnel-arrow">→</div>;
}

function Insight({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div className="insight">
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  );
}

function formatEvent(event: string) {
  const names: Record<string, string> = {
    click: "Переход по рекламе",
    bot_start: "Запуск бота",
    lead: "Создание лида",
  };

  return names[event] ?? event;
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("ru-RU");
}

export default App;