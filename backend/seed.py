import sqlite3
import random
import csv
from pathlib import Path
from datetime import datetime, timedelta

from openpyxl import load_workbook


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "marketing.db"
EXCEL_PATH =  BASE_DIR / "base.xlsx"


random.seed(42)


# ============================================================
# HELPERS
# ============================================================

def parse_datetime(value):
    if isinstance(value, datetime):
        return value

    value = str(value).strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Не удалось распознать дату: {value}")


def get_random_date_in_range(start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")

    delta = end - start

    random_days = random.randrange(max(1, delta.days))

    result = start + timedelta(
        days=random_days,
        hours=random.randint(8, 20),
        minutes=random.randint(0, 59)
    )

    return result.strftime("%Y-%m-%d %H:%M:%S")


def generate_funnel_dates(purchase_date_str, publication_date_str):
    """
    Генерирует:

        click
          ↓
        bot_start
          ↓
        lead
          ↓
        purchase

    Все события гарантированно находятся:
        publication <= click < bot < lead < purchase
    """

    purchase_date = parse_datetime(purchase_date_str)
    publication_date = parse_datetime(publication_date_str)

    # Максимально возможная дата клика —
    # хотя бы 30 минут до покупки.
    latest_click = purchase_date - timedelta(
        hours=random.randint(12, 72)
    )

    if latest_click <= publication_date:
        latest_click = publication_date + timedelta(
            minutes=random.randint(5, 60)
        )

    # Если между публикацией и покупкой совсем мало времени
    if latest_click >= purchase_date:
        latest_click = purchase_date - timedelta(
            minutes=30
        )

    # Выбираем click между publication и purchase
    available_seconds = int(
        (latest_click - publication_date).total_seconds()
    )

    if available_seconds <= 0:
        click_date = publication_date
    else:
        click_date = publication_date + timedelta(
            seconds=random.randint(
                1,
                max(1, available_seconds)
            )
        )

    # Bot start после click
    bot_start_date = click_date + timedelta(
        minutes=random.randint(2, 15)
    )

    # Lead после bot
    lead_date = bot_start_date + timedelta(
        hours=random.randint(1, 6),
        minutes=random.randint(5, 30)
    )

    # Если lead оказался после покупки —
    # ставим его гарантированно до покупки.
    if lead_date >= purchase_date:
        lead_date = purchase_date - timedelta(
            minutes=random.randint(10, 60)
        )

    # Защита от невозможной последовательности
    if lead_date <= bot_start_date:
        lead_date = bot_start_date + timedelta(minutes=1)

    if bot_start_date <= click_date:
        bot_start_date = click_date + timedelta(minutes=2)

    return [
        click_date.strftime("%Y-%m-%d %H:%M:%S"),
        bot_start_date.strftime("%Y-%m-%d %H:%M:%S"),
        lead_date.strftime("%Y-%m-%d %H:%M:%S")
    ]


# ============================================================
# IMPORT BASE.XLSX -> SALES
# ============================================================

# ============================================================
# IMPORT SALES MART -> SALES
# ============================================================

def import_sales_from_mart(cursor):
    MART_PATH = BASE_DIR / "data" / "sales_mart.csv"

    if not MART_PATH.exists():
        raise FileNotFoundError(
            f"Файл sales_mart_format.csv не найден: {MART_PATH}"
        )

    print(f"Читаем продажи из витрины: {MART_PATH}")

    # Пересоздаём sales
    cursor.execute("DROP TABLE IF EXISTS sales")

    cursor.execute("""
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            amount REAL NOT NULL,
            course TEXT,
            purchased_at TEXT NOT NULL
        )
    """)

    inserted_count = 0

    with open(MART_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        for row_number, row in enumerate(reader, start=2):
            student_id = row.get("student_id", "").strip()
            amount_str = row.get("order_revenue", "").strip()
            course = row.get("courses", "").strip()
            purchased_at = row.get("timestamp", "").strip()

            # Пропускаем, если нет обязательных полей
            if not student_id or not amount_str or not purchased_at:
                continue

            try:
                amount = float(amount_str)
            except ValueError:
                print(f"Строка {row_number}: пропущена — некорректная сумма: {amount_str}")
                continue

            # Обрабатываем дату уже существующим хелпером parse_datetime
            try:
                dt = parse_datetime(purchased_at)
                purchased_at_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                purchased_at_formatted = purchased_at

            cursor.execute("""
                INSERT INTO sales (
                    student_id,
                    amount,
                    course,
                    purchased_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                student_id,
                amount,
                course,
                purchased_at_formatted
            ))

            inserted_count += 1

    print(f"Импортировано сгруппированных продаж: {inserted_count}")

    # Проверка
    cursor.execute("SELECT COUNT(*) FROM sales")
    sales_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM sales")
    students_count = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(purchased_at), MAX(purchased_at) FROM sales")
    min_date, max_date = cursor.fetchone()

    print(f"Всего заказов (сгруппированных): {sales_count}")
    print(f"Уникальных студентов: {students_count}")
    print(f"Период продаж: {min_date} — {max_date}")

    return sales_count

# ============================================================
# MAIN
# ============================================================

def seed_synthetic_data():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:

        # ====================================================
        # IMPORT SALES
        # ====================================================

        import_sales_from_mart(cursor)

        # ====================================================
        # CREATE SYNTHETIC TABLES
        # ====================================================

        cursor.executescript(
            """
            DROP TABLE IF EXISTS attribution;
            DROP TABLE IF EXISTS marketing_touches;
            DROP TABLE IF EXISTS synthetic_placements;
            DROP TABLE IF EXISTS synthetic_campaigns;


            CREATE TABLE synthetic_campaigns (
                campaign_id TEXT PRIMARY KEY,
                name TEXT,
                channel TEXT,
                start_at TEXT,
                end_at TEXT,
                budget REAL,
                is_synthetic INTEGER
            );


            CREATE TABLE synthetic_placements (
                placement_id TEXT PRIMARY KEY,
                campaign_id TEXT,
                platform TEXT,
                channel_name TEXT,
                creative_id TEXT,
                tracking_id TEXT,
                publication_time TEXT,
                cost REAL,
                impressions INTEGER,
                clicks INTEGER,
                is_synthetic INTEGER
            );


            CREATE TABLE marketing_touches (
                touch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                placement_id TEXT NOT NULL,
                creative_id TEXT NOT NULL,
                tracking_id TEXT NOT NULL,
                student_id TEXT,
                touched_at TEXT NOT NULL,
                event_type TEXT NOT NULL
            );


            CREATE TABLE attribution (
                attribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                touch_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                sale_id INTEGER NOT NULL UNIQUE,
                attributed_revenue REAL NOT NULL,
                attribution_model TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        print("🧹 Старые synthetic-таблицы очищены.")

        # ====================================================
        # CAMPAIGNS
        # ====================================================

        campaigns = [
            (
                "CAMP_TG_AUTUMN",
                "Осенняя распродажа",
                "Telegram",
                "2026-08-01",
                "2026-09-30",
                150000
            ),
            (
                "CAMP_TG_ML",
                "Промо ML курса",
                "Telegram",
                "2026-08-05",
                "2026-09-15",
                100000
            ),
            (
                "CAMP_TG_ANALYTICS",
                "Аналитика старт",
                "Telegram",
                "2026-08-10",
                "2026-09-20",
                80000
            )
        ]

        cursor.executemany(
            """
            INSERT INTO synthetic_campaigns
            (
                campaign_id,
                name,
                channel,
                start_at,
                end_at,
                budget,
                is_synthetic
            )
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            campaigns
        )

        # ====================================================
        # PLACEMENTS
        # ====================================================

        placements = [
            (
                "PLAC_TG_ML_001",
                "CAMP_TG_ML",
                "Telegram",
                "Data Science Today",
                "CR_ML_1",
                "TR_ML_1",
                "2026-08-04 10:00:00",
                15000
            ),
            (
                "PLAC_TG_ML_002",
                "CAMP_TG_ML",
                "Telegram",
                "AI & ML Community",
                "CR_ML_2",
                "TR_ML_2",
                "2026-08-12 14:30:00",
                20000
            ),
            (
                "PLAC_TG_ANALYTICS_001",
                "CAMP_TG_ANALYTICS",
                "Telegram",
                "Аналитика для всех",
                "CR_AN_1",
                "TR_AN_1",
                "2026-08-08 09:15:00",
                12000
            ),
            (
                "PLAC_TG_ANALYTICS_002",
                "CAMP_TG_ANALYTICS",
                "Telegram",
                "Junior Analyst",
                "CR_AN_2",
                "TR_AN_2",
                "2026-08-18 18:00:00",
                18000
            ),
            (
                "PLAC_TG_BACKEND_001",
                "CAMP_TG_AUTUMN",
                "Telegram",
                "Python Backend",
                "CR_BK_1",
                "TR_BK_1",
                "2026-08-25 11:00:00",
                25000
            ),
            (
                "PLAC_TG_BACKEND_002",
                "CAMP_TG_AUTUMN",
                "Telegram",
                "IT Jobs",
                "CR_BK_2",
                "TR_BK_2",
                "2026-09-01 10:00:00",
                10000
            )
        ]

        for placement in placements:
            cursor.execute(
                """
                INSERT INTO synthetic_placements
                (
                    placement_id,
                    campaign_id,
                    platform,
                    channel_name,
                    creative_id,
                    tracking_id,
                    publication_time,
                    cost,
                    impressions,
                    clicks,
                    is_synthetic
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    placement[0],
                    placement[1],
                    placement[2],
                    placement[3],
                    placement[4],
                    placement[5],
                    placement[6],
                    placement[7],
                    random.randint(5000, 15000),
                    random.randint(100, 500)
                )
            )

        # ====================================================
        # LOAD SALES
        # ====================================================

        cursor.execute(
            """
            SELECT
                sale_id,
                student_id,
                amount,
                purchased_at
            FROM sales
            ORDER BY purchased_at ASC
            """
        )

        all_sales = cursor.fetchall()

        if not all_sales:
            raise ValueError(
                "❌ В sales нет продаж."
            )

        distinct_students = list(
            set(
                sale[1]
                for sale in all_sales
            )
        )

        print(
            f"💰 Продаж: {len(all_sales)}"
        )

        print(
            f"👥 Уникальных покупателей: "
            f"{len(distinct_students)}"
        )

        # ====================================================
        # FIRST PURCHASE FOR EACH STUDENT
        # ====================================================

        first_purchase_by_student = {}

        for sale in all_sales:

            sale_id = sale[0]
            student_id = sale[1]
            amount = sale[2]
            purchased_at = sale[3]

            if student_id not in first_purchase_by_student:
                first_purchase_by_student[student_id] = sale
            else:
                old_sale = first_purchase_by_student[
                    student_id
                ]

                old_date = parse_datetime(
                    old_sale[3]
                )

                new_date = parse_datetime(
                    purchased_at
                )

                if new_date < old_date:
                    first_purchase_by_student[
                        student_id
                    ] = sale

        # ====================================================
        # SELECT REAL MARKETING BUYERS
        # ====================================================

        # Берём примерно 55% реальных покупателей.
        #
        # Это не фиксированное количество.
        # Оно зависит от base.xlsx.

        marketing_buyer_count = round(
            len(distinct_students) * 0.55
        )

        marketing_buyer_count = max(
            1,
            marketing_buyer_count
        )

        marketing_buyer_count = min(
            marketing_buyer_count,
            len(distinct_students)
        )

        selected_real_students = random.sample(
            distinct_students,
            marketing_buyer_count
        )

        print(
            f"🎯 Покупателей в маркетинговой воронке: "
            f"{len(selected_real_students)}"
        )

        # ====================================================
        # AVAILABLE PLACEMENTS
        # ====================================================

        def get_available_placement(
            target_date_str
        ):
            target_date = parse_datetime(
                target_date_str
            )

            available = [
                p
                for p in placements
                if parse_datetime(p[6]) <= target_date
            ]

            if not available:
                return None

            return random.choice(available)

        # ====================================================
        # INSERT TOUCH
        # ====================================================

        touches_inserted = 0

        def insert_touch(
            c_id,
            p_id,
            cr_id,
            tr_id,
            s_id,
            t_at,
            e_type
        ):
            nonlocal touches_inserted

            cursor.execute(
                """
                INSERT INTO marketing_touches
                (
                    campaign_id,
                    placement_id,
                    creative_id,
                    tracking_id,
                    student_id,
                    touched_at,
                    event_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    c_id,
                    p_id,
                    cr_id,
                    tr_id,
                    s_id,
                    t_at,
                    e_type
                )
            )

            touches_inserted += 1

            return cursor.lastrowid

        # ====================================================
        # REAL BUYER FUNNEL
        # ====================================================

        #
        # Ключевое отличие от старого генератора:
        #
        # BUYER ОБЯЗАТЕЛЬНО проходит:
        #
        # click
        #   ↓
        # bot_start
        #   ↓
        # lead
        #   ↓
        # purchase
        #
        # Поэтому:
        #
        # buyers <= leads <= bot_start <= clicks
        #

        buyer_attributions = []

        for student_id in selected_real_students:

            sale = first_purchase_by_student[
                student_id
            ]

            sale_id = sale[0]
            amount = sale[2]
            purchased_at = sale[3]

            purchase_date = parse_datetime(
                purchased_at
            )

            placement = get_available_placement(
                purchased_at
            )

            if placement is None:
                continue

            publication_date = parse_datetime(
                placement[6]
            )

            # Если публикация слишком близко к покупке,
            # всё равно создаём нормальную временную цепочку.
            earliest_click = publication_date + timedelta(
                minutes=5
            )

            latest_lead = purchase_date - timedelta(
                minutes=10
            )

            if earliest_click >= latest_lead:
                continue

            available_seconds = int(
                (
                    latest_lead -
                    earliest_click
                ).total_seconds()
            )

            click_date = (
                earliest_click +
                timedelta(
                    seconds=random.randint(
                        0,
                        max(1, available_seconds)
                    )
                )
            )

            bot_start_date = click_date + timedelta(
                minutes=random.randint(2, 15)
            )

            lead_date = bot_start_date + timedelta(
                hours=random.randint(1, 4),
                minutes=random.randint(5, 30)
            )

            # Гарантируем lead до purchase
            if lead_date >= purchase_date:
                lead_date = purchase_date - timedelta(
                    minutes=random.randint(10, 60)
                )

            # Гарантируем порядок
            if lead_date <= bot_start_date:
                lead_date = bot_start_date + timedelta(
                    minutes=1
                )

            # CLICK
            click_touch_id = insert_touch(
                placement[1],
                placement[0],
                placement[4],
                placement[5],
                student_id,
                click_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "click"
            )

            # BOT
            insert_touch(
                placement[1],
                placement[0],
                placement[4],
                placement[5],
                student_id,
                bot_start_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "bot_start"
            )

            # LEAD
            lead_touch_id = insert_touch(
                placement[1],
                placement[0],
                placement[4],
                placement[5],
                student_id,
                lead_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "lead"
            )

            # Для last-touch атрибуции используем именно lead,
            # потому что это последнее маркетинговое касание.
            buyer_attributions.append(
                (
                    lead_touch_id,
                    student_id,
                    sale_id,
                    amount
                )
            )

        # ====================================================
        # SYNTHETIC NON-BUYERS
        # ====================================================

        #
        # Здесь генерируем пользователей,
        # которые могут дойти до lead,
        # но покупки у них нет.
        #

        fake_users_count = max(
            100,
            len(selected_real_students) * 3
        )

        for i in range(fake_users_count):

            fake_student = f"synth_user_{i}"

            placement = random.choice(
                placements
            )

            publication_date = parse_datetime(
                placement[6]
            )

            # Касание только после публикации
            click_date = publication_date + timedelta(
                days=random.randint(0, 10),
                hours=random.randint(1, 12),
                minutes=random.randint(0, 59)
            )

            insert_touch(
                placement[1],
                placement[0],
                placement[4],
                placement[5],
                fake_student,
                click_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "click"
            )

            # 60% запускают бота
            if random.random() < 0.60:

                bot_date = click_date + timedelta(
                    minutes=random.randint(1, 15)
                )

                insert_touch(
                    placement[1],
                    placement[0],
                    placement[4],
                    placement[5],
                    fake_student,
                    bot_date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "bot_start"
                )

                # 30% оставляют лид
                if random.random() < 0.30:

                    lead_date = bot_date + timedelta(
                        minutes=random.randint(10, 180)
                    )

                    insert_touch(
                        placement[1],
                        placement[0],
                        placement[4],
                        placement[5],
                        fake_student,
                        lead_date.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "lead"
                    )

        print(
            f"📊 Сгенерировано касаний: "
            f"{touches_inserted}"
        )

        # ====================================================
        # ATTRIBUTION
        # ====================================================

        #
        # ВАЖНО:
        #
        # Старый код делал:
        #
        # for sale in ALL sales:
        #     найти touch
        #     INSERT attribution
        #
        # Из-за этого один student мог иметь:
        #
        # sale 1 -> attribution
        # sale 2 -> attribution
        # sale 3 -> attribution
        # sale 4 -> attribution
        #
        # Теперь attribution создаётся ТОЛЬКО:
        #
        # selected buyer
        # +
        # first purchase
        # +
        # last touch = lead
        #

        attributions_count = 0

        for (
            touch_id,
            student_id,
            sale_id,
            amount
        ) in buyer_attributions:

            cursor.execute(
                """
                INSERT INTO attribution
                (
                    touch_id,
                    student_id,
                    sale_id,
                    attributed_revenue,
                    attribution_model,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    touch_id,
                    student_id,
                    sale_id,
                    amount,
                    "last_touch"
                )
            )

            attributions_count += 1

        print(
            f"🔗 Создано attribution: "
            f"{attributions_count}"
        )

        # ====================================================
        # DEBUG CHECKS
        # ====================================================

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM attribution
            """
        )

        attribution_rows = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(DISTINCT student_id)
            FROM attribution
            """
        )

        attributed_buyers = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(DISTINCT sale_id)
            FROM attribution
            """
        )

        attributed_sales = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COALESCE(SUM(attributed_revenue), 0)
            FROM attribution
            """
        )

        attributed_revenue = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM marketing_touches
            WHERE event_type = 'click'
            """
        )

        clicks = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM marketing_touches
            WHERE event_type = 'bot_start'
            """
        )

        bot_starts = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM marketing_touches
            WHERE event_type = 'lead'
            """
        )

        leads = cursor.fetchone()[0]

        print()
        print("=" * 60)
        print("📊 FUNNEL")
        print("=" * 60)

        print(f"Clicks:       {clicks}")
        print(f"Bot starts:   {bot_starts}")
        print(f"Leads:        {leads}")
        print(f"Buyers:       {attributed_buyers}")
        print(f"Revenue:      {attributed_revenue:,.2f} ₽")

        print()
        print("=" * 60)
        print("🔒 DATA CHECK")
        print("=" * 60)

        print(
            f"Attribution rows:       {attribution_rows}"
        )

        print(
            f"Unique attributed sales: {attributed_sales}"
        )

        print(
            f"Unique attributed buyers: {attributed_buyers}"
        )

        if attribution_rows != attributed_sales:
            print(
                "⚠️ ВНИМАНИЕ: есть дубли sale_id!"
            )
        else:
            print(
                "✅ Дубликатов sale_id в attribution нет."
            )

        if attributed_buyers > leads:
            print(
                "⚠️ ВНИМАНИЕ: buyers > leads!"
            )
        else:
            print(
                "✅ Funnel логичен: buyers <= leads."
            )

        conn.commit()

        print()
        print(
            "✅ Сидирование успешно завершено!"
        )
        print(
            f"📁 БД: {DB_PATH}"
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    seed_synthetic_data()
