# Marketing Data Model — Postupashki

`src/models.py` описывает целевую структуру marketing measurement system через SQLAlchemy ORM.

Текущий backend MVP продолжает использовать SQLite как рабочее хранилище. Это не конфликт: SQLite — конкретная СУБД, а SQLAlchemy - ORM-слой для описания и работы с данными.

В рамках хакатона существующий backend не мигрируется на новую ORM-схему. Для задач 6 и 8 расчёт attribution и ROMI выполняется отдельно через CSV и pandas.

## Data flow

Основная цепочка данных:

```text
MarketingActivity
        ↓
Placement
        ↓
UserTouch
        ↓
User
        ↓
Payment
        ↓
PaymentAttribution
```

Дополнительные сущности:

```text
Creative
Lead
LeadEvent
Refund
```

Основные связи:

```text
Placement.campaign_id
    -> MarketingActivity.campaign_id

Placement.creative_id
    -> Creative.creative_id

UserTouch.placement_id
    -> Placement.placement_id

UserTouch.user_id
    -> User.user_id

Lead.user_id
    -> User.user_id

LeadEvent.lead_id
    -> Lead.lead_id

Payment.user_id
    -> User.user_id

Refund.payment_id
    -> Payment.payment_id

PaymentAttribution.payment_id
    -> Payment.payment_id

PaymentAttribution.touch_id
    -> UserTouch.touch_id
```

`PaymentAttribution` связывает конкретную оплату с конкретным маркетинговым касанием.

Кампания, creative, channel и publisher определяются через `Placement`.

## MarketingActivity

Таблица:

```text
marketing_activity
```

Поля:

```text
campaign_id
campaign_name
start_at
end_at
planned_budget
goal
```

`goal` принимает значения:

```text
awareness
conversion
```

Ограничения:

```text
end_at IS NULL
OR start_at IS NULL
OR end_at >= start_at

planned_budget IS NULL
OR planned_budget >= 0
```

## Creative

Таблица:

```text
creative
```

Поля:

```text
creative_id
name
text
offer
destination_url
```

Tracking token здесь не хранится, потому что он относится не к creative, а к конкретному placement.

## Placement

Таблица:

```text
placement
```

Поля:

```text
placement_id
campaign_id
creative_id
channel
publisher
publication_at
cost
tracking_token
```

Пример:

```text
channel = telegram
publisher = tg_channel_a
```

`tracking_token` уникален для placement и позволяет связывать внешний marketing activity с user touch.

Ограничение:

```text
cost >= 0
```

## User

Таблица:

```text
app_user
```

Поля:

```text
user_id
telegram_user_hash
first_seen_at
```

Для user stitching используется стабильный идентификатор пользователя.

В production-сценарии Telegram user id должен храниться в виде hash, чтобы не использовать лишние персональные данные.

Username не подходит как основной стабильный идентификатор, потому что пользователь может его изменить или удалить.

## UserTouch

Таблица:

```text
user_touch
```

Поля:

```text
touch_id
user_id
anonymous_id
placement_id
event_type
occurred_at
external_event_id
```

`event_type`:

```text
view
click
bot_start
```

До идентификации пользователя касание может существовать только с `anonymous_id`.

Ограничение:

```text
user_id IS NOT NULL
OR anonymous_id IS NOT NULL
```

`campaign_id`, `creative_id`, `channel` и `publisher` в `UserTouch` отдельно не дублируются.

Они определяются через:

```text
UserTouch.placement_id
    -> Placement
```

## Lead

Таблица:

```text
lead
```

Поля:

```text
lead_id
user_id
status
created_at
```

`status`:

```text
new
contacted
qualified
won
lost
```

`Lead` хранит текущее состояние лида.

История изменений хранится в `LeadEvent`.

## LeadEvent

Таблица:

```text
lead_event
```

Поля:

```text
event_id
lead_id
event_type
occurred_at
manager_id
```

`event_type`:

```text
conversation_started
manager_assigned
qualified
offer_sent
won
lost
```

## Payment

Таблица:

```text
payment
```

Поля:

```text
payment_id
order_id
user_id
amount
currency
course
status
paid_at
created_at
external_payment_id
```

`status`:

```text
pending
succeeded
failed
refunded
partially_refunded
```

Ограничение:

```text
amount >= 0
```

В модели предусмотрены вычисляемые свойства:

```text
refunded_amount
net_amount
```

Формула:

```text
net_amount =
    payment.amount
    - sum(refund.amount)
```

## Refund

Таблица:

```text
refund
```

Поля:

```text
refund_id
payment_id
amount
refunded_at
reason
```

Ограничение:

```text
amount > 0
```

## PaymentAttribution

Таблица:

```text
payment_attribution
```

Поля:

```text
attribution_id
payment_id
touch_id
model
weight
attribution_window_days
calculated_at
```

SQLAlchemy-модель поддерживает:

```text
first_touch
last_touch
linear
```

Ограничения:

```text
0 < weight <= 1

attribution_window_days > 0
```

Также действует уникальность:

```text
payment_id
touch_id
model
```

Часть attribution-правил нельзя корректно выразить обычным SQL CHECK.

Касание должно:

```text
относиться к тому же пользователю
произойти не позже оплаты
попадать в attribution window
```

Для multi-touch модели:

```text
sum(weight) = 1
```

Эти проверки выполняются на уровне аналитического кода.

## Analytical attribution models

В задаче 6 сравниваются пять моделей:

```text
first_touch
last_touch
linear
time_decay
position_based
```

Первые три также представлены в SQLAlchemy enum.

`time_decay` и `position_based` используются только в аналитическом слое:

```text
src/attribution.py
```

Они сохраняются в CSV и не записываются в таблицу `payment_attribution`.

### First Touch

Первое допустимое касание получает:

```text
100% attribution weight
```

### Last Touch

Последнее допустимое касание получает:

```text
100% attribution weight
```

### Linear

Вес распределяется поровну между всеми допустимыми касаниями.

Например, для трёх touches:

```text
1/3
1/3
1/3
```

### Time Decay

Чем ближе touch к покупке, тем выше его вес.

В MVP используется half-life:

```text
7 дней
```

Формула:

```text
weight_raw =
    0.5 ^ (
        age_days / half_life_days
    )
```

После этого веса нормализуются так, чтобы:

```text
sum(weight) = 1
```

### Position Based

Для одного касания:

```text
100%
```

Для двух:

```text
50%
50%
```

Для трёх и более:

```text
40% first touch
40% last touch
20% between middle touches
```

## Attribution window

Основное attribution window:

```text
30 дней
```

Sensitivity analysis дополнительно проверяет:

```text
7
14
30
60
90 дней
```

Для покупки учитываются только касания:

```text
того же пользователя
occurred_at <= purchase_time
occurred_at >= purchase_time - attribution_window
```

Если подходящих касаний нет, заказ остаётся unattributed.

Каждая повторная покупка рассматривается как отдельный заказ со своим attribution window.

## Attribution invariants

Для каждого атрибутированного заказа должны выполняться условия:

```text
sum(weight) = 1
```

и:

```text
sum(attributed_revenue)
    = order_revenue
```

Проверка выполняется в:

```text
src/attribution.py
```

## ROMI

Основная метрика:

```text
ROMI_attr =
    (
        Attributed Revenue
        - Marketing Cost
    )
    / Marketing Cost
```

Marketing cost берётся на уровне placement.

Стоимость placement учитывается один раз независимо от количества attribution rows.

Если:

```text
cost = 0
```

ROMI не определяется.

## Contribution margin scenario

В исходных данных нет contribution margin.

Поэтому дополнительно используется сценарный расчёт:

```text
Attributed Contribution =
    Attributed Revenue
    * contribution_margin_rate
```

и:

```text
ROMI_contribution =
    (
        Attributed Contribution
        - Marketing Cost
    )
    / Marketing Cost
```

Основной сценарий:

```text
contribution_margin_rate = 0.6
```

Sensitivity analysis:

```text
0.4
0.5
0.6
0.7
```

Эти значения являются аналитическими сценариями, а не наблюдаемыми фактами.

## Real and synthetic data

Реальные данные:

```text
data/sales_mart.csv
```

В них находятся реальные reconstructed orders:

```text
order_id
student_id
timestamp
courses
n_courses
order_revenue
is_bundle
order_number
is_repeat_order
days_since_previous_order
```

Marketing history является synthetic:

```text
data/mock_placements.csv
data/mock_touches.csv
```

Это связано с тем, что в исходных данных отсутствует полный исторический журнал:

```text
рекламных размещений
стоимости размещений
user touches
campaign identifiers
creative identifiers
```

Synthetic marketing data нужны для демонстрации того, как должна работать measurement system.

Они не являются реконструкцией реальных исторических рекламных кампаний.

## Analytical pipeline

```text
data/sales_mart.csv
        +
data/mock_placements.csv
        +
data/mock_touches.csv
        ↓
src/io_utils.py
        ↓
src/attribution.py
        ↓
data/attribution_results.csv
        ↓
src/romi.py
        ↓
ROMI outputs
```

Все этапы объединены в:

```text
src/pipeline.py
```

Запуск из корня проекта:

```bash
python run_tasks_6_8.py
```

## Outputs

После запуска формируются:

```text
data/mock_placements.csv
data/mock_touches.csv

data/attribution_results.csv
data/attribution_coverage.csv

data/romi_by_placement.csv
data/romi_by_campaign.csv
data/romi_by_publisher.csv

data/romi_sensitivity.csv
```

## Attribution and incrementality

Attribution не является причинной оценкой.

Attribution отвечает на вопрос:

```text
как распределить наблюдаемую revenue
между marketing touches
```

Она не отвечает на вопрос:

```text
произошла бы покупка без рекламы
```

Поэтому рассчитанная метрика называется:

```text
ROMI_attr
```

а не incremental ROMI.

`ROMI_inc` по текущим историческим данным не идентифицируется.

Для оценки incrementality нужен causal design, например:

```text
A/B test
randomized holdout
geo holdout
randomized promotion
```

## SQLite and SQLAlchemy

Существующий backend продолжает использовать SQLite.

`src/models.py` не является миграцией текущего `marketing.db`.

Он описывает целевую production-ready data model marketing measurement system.

Для задач 6 и 8 runtime-расчёт выполняется через CSV и pandas.

Такое разделение позволяет сохранить работающий MVP и одновременно показать целевую архитектуру системы.